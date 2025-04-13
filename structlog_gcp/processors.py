# https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
# https://cloud.google.com/logging/docs/agent/logging/configuration#process-payload
# https://cloud.google.com/logging/docs/structured-logging#special-payload-fields


import structlog.processors
from structlog.typing import EventDict, Processor, WrappedLogger

from .constants import CLOUD_LOGGING_KEY, SEVERITY_MAPPING, SOURCE_LOCATION_KEY


def setup_code_location() -> list[Processor]:
    call_site_processors = structlog.processors.CallsiteParameterAdder(
        parameters=[
            structlog.processors.CallsiteParameter.PATHNAME,
            structlog.processors.CallsiteParameter.MODULE,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        ]
    )

    return [call_site_processors, code_location]


def init_cloud_logging(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Initialize the Google Cloud Logging event message"""

    value = {
        "message": event_dict.pop("event"),
        "time": event_dict.pop("timestamp"),
    }

    event_dict[CLOUD_LOGGING_KEY] = value
    return event_dict


def finalize_cloud_logging(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Finalize the Google Cloud Logging event message and replace the logging event.

    This is not exactly the format the Cloud Logging directly ingests, but
    Cloud Logging is smart enough to transform basic JSON-like logging events
    into Cloud Logging-compatible events.

    See: https://cloud.google.com/logging/docs/structured-logging#special-payload-fields
    """

    # Take out the Google Cloud Logging set of fields from the event dict
    gcp_event: EventDict = event_dict.pop(CLOUD_LOGGING_KEY)

    # Override whatever is left from the event dict with the content of all
    # the Google Cloud Logging-formatted fields.
    event_dict.update(gcp_event)

    # Fields which are not known by Google Cloud Logging will be added to
    # the `jsonPayload` field.
    #
    # See the `message` field documentation in:
    # https://cloud.google.com/logging/docs/structured-logging#special-payload-fields

    return event_dict


class LogSeverity:
    """Set the severity using the Google Cloud Logging severities.


    See: https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity
    """

    def __init__(self) -> None:
        self.default = "notset"
        self.mapping = SEVERITY_MAPPING.copy()

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        """Format a Python log level value as a GCP log severity."""

        log_level = method_name
        severity = self.mapping.get(log_level, self.default)

        event_dict[CLOUD_LOGGING_KEY]["severity"] = severity
        return event_dict


def code_location(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Inject the location of the logging message into the logs"""

    location = {
        "file": event_dict.pop("pathname"),
        "line": str(event_dict.pop("lineno")),
        "function": f"{event_dict.pop('module')}:{event_dict.pop('func_name')}",
    }

    event_dict[CLOUD_LOGGING_KEY][SOURCE_LOCATION_KEY] = location

    return event_dict
