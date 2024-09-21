import structlog.processors
from structlog.typing import Processor

from . import error_reporting, processors


def build_processors(
    service: str | None = None,
    version: str | None = None,
) -> list[Processor]:
    procs: list[Processor] = []

    # Add a timestamp in ISO 8601 format.
    procs.append(structlog.processors.TimeStamper(fmt="iso"))
    procs.append(processors.init_cloud_logging)

    procs.extend(processors.setup_log_severity())
    procs.extend(processors.setup_code_location())

    # Errors: log exceptions
    procs.extend(error_reporting.setup_exceptions())

    # Errors: formatter for Error Reporting
    procs.append(error_reporting.ReportError(["CRITICAL"]))

    # Errors: add service context
    procs.append(error_reporting.ServiceContext(service, version))

    # Finally: Cloud Logging formatter
    procs.append(processors.finalize_cloud_logging)

    # Format as JSON
    procs.append(structlog.processors.JSONRenderer())

    return procs
