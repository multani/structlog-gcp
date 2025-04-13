import structlog.contextvars
import structlog.processors
from structlog.typing import Processor

from . import error_reporting, processors


def build_processors(
    service: str | None = None,
    version: str | None = None,
) -> list[Processor]:
    """Build structlog processors to export logs for Google Cloud Logging.

    This builder function is expected to be your go-to function to expose structlog logs to Google
    Cloud Logging format.

    It configures the Google Cloud Logging-specific processors but also good defaults processors.

    If you need more control over which processors are exactly configured, check the
    :ref:`build_gcp_processors` function.
    """

    procs: list[Processor] = []

    procs.append(structlog.contextvars.merge_contextvars)
    procs.extend(build_gcp_processors(service, version))
    procs.append(structlog.processors.JSONRenderer())

    return procs


def build_gcp_processors(
    service: str | None = None,
    version: str | None = None,
) -> list[Processor]:
    """Build only the Google Cloud Logging-specific processors.

    This builds a set of processors to format logs according to what Google Cloud Logging expects.

    See: https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs

    Use this builder function if you want to customize the processors before and after the
    GCP-specific processors.

    In particular, this builder function **doesn't** configure the final JSON renderer. You are
    expected to provide your own.

    For a simpler, more general alternative, use :ref:`build_processors` instead.
    """

    procs: list[Processor] = []

    # Add a timestamp in ISO 8601 format.
    procs.append(structlog.processors.TimeStamper(fmt="iso"))
    procs.append(processors.init_cloud_logging)

    procs.append(processors.LogSeverity())
    procs.extend(processors.setup_code_location())

    # Errors: log exceptions
    procs.extend(error_reporting.setup_exceptions())

    # Errors: formatter for Error Reporting
    procs.append(error_reporting.ReportError(["CRITICAL"]))

    # Errors: add service context
    procs.append(error_reporting.ServiceContext(service, version))

    # Finally: Cloud Logging formatter
    procs.append(processors.finalize_cloud_logging)

    return procs
