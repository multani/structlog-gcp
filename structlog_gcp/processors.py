# https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
# https://cloud.google.com/logging/docs/agent/logging/configuration#process-payload
# https://cloud.google.com/logging/docs/structured-logging#special-payload-fields


import structlog.processors
from structlog.typing import EventDict, Processor, WrappedLogger

from .types import CLOUD_LOGGING_KEY, SOURCE_LOCATION_KEY


class CoreCloudLogging:
    """Initialize the Google Cloud Logging event message"""

    def setup(self) -> list[Processor]:
        return [
            # If some value is in bytes, decode it to a unicode str.
            structlog.processors.UnicodeDecoder(),
            # Add a timestamp in ISO 8601 format.
            structlog.processors.TimeStamper(fmt="iso"),
            self,
        ]

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        value = {
            "message": event_dict.pop("event"),
            "time": event_dict.pop("timestamp"),
        }

        event_dict[CLOUD_LOGGING_KEY] = value
        return event_dict


class FormatAsCloudLogging:
    """Finalize the Google Cloud Logging event message and replace the logging event.

    This is not exactly the format the Cloud Logging directly ingests, but
    Cloud Logging is smart enough to transform basic JSON-like logging events
    into Cloud Logging-compatible events.

    See: https://cloud.google.com/logging/docs/structured-logging#special-payload-fields
    """

    def setup(self) -> list[Processor]:
        return [self]

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        # Take out the Google Cloud Logging set of fields from the event dict
        gcp_event: EventDict = event_dict.pop(CLOUD_LOGGING_KEY)

        # Override whatever is left from the event dict with the content of all
        # the Google Cloud Logging-formatted fields.
        event_dict.update(gcp_event)

        # Fields which are not known by Google Cloud Logging will be added to
        # the `jsonPayload` field.
        # See the `message` field documentation in:
        # https://cloud.google.com/logging/docs/structured-logging#special-payload-fields

        return event_dict


class LogSeverity:
    """Set the severity using the Google Cloud Logging severities"""

    def __init__(self) -> None:
        self.default = "notset"

        # From Python's logging level to Google level
        self.mapping = {
            "notset": "DEFAULT",  # The log entry has no assigned severity level.
            "debug": "DEBUG",  # Debug or trace information.
            "info": "INFO",  # Routine information, such as ongoing status or performance.
            # "notice": "NOTICE", # Normal but significant events, such as start up, shut down, or a configuration change.
            "warn": "WARNING",  # Warning events might cause problems.
            "warning": "WARNING",  # Warning events might cause problems.
            "error": "ERROR",  # Error events are likely to cause problems.
            "critical": "CRITICAL",  # Critical events cause more severe problems or outages.
            # "alert": "ALERT", # A person must take an action immediately.
            # "emergency": "EMERGENCY", #	One or more systems are unusable.
        }

    def setup(self) -> list[Processor]:
        # Add log level to event dict.
        return [structlog.processors.add_log_level, self]

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        """Format a Python log level value as a GCP log severity.

        See: https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity
        """

        log_level = event_dict.pop("level")
        severity = self.mapping.get(log_level, self.default)

        event_dict[CLOUD_LOGGING_KEY]["severity"] = severity
        return event_dict


class CodeLocation:
    """Inject the location of the logging message into the logs"""

    def setup(self) -> list[Processor]:
        # Add callsite parameters.
        call_site_proc = structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        )
        return [call_site_proc, self]

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        location = {
            "file": event_dict.pop("pathname"),
            "line": str(event_dict.pop("lineno")),
            "function": f"{event_dict.pop('module')}:{event_dict.pop('func_name')}",
        }

        event_dict[CLOUD_LOGGING_KEY][SOURCE_LOCATION_KEY] = location

        return event_dict
