# https://cloud.google.com/functions/docs/monitoring/logging#writing_structured_logs
# https://cloud.google.com/logging/docs/agent/logging/configuration#process-payload
# https://cloud.google.com/logging/docs/structured-logging#special-payload-fields

import structlog.processors

from .types import CLOUD_LOGGING_KEY, SOURCE_LOCATION_KEY


class CoreCloudLogging:
    """Initialize the Google Cloud Logging event message"""

    def setup(self):
        return [
            # If some value is in bytes, decode it to a unicode str.
            structlog.processors.UnicodeDecoder(),
            # Add a timestamp in ISO 8601 format.
            structlog.processors.TimeStamper(fmt="iso"),
            self.__call__,
        ]

    def __call__(self, logger, method_name, event_dict):
        value = {
            "message": event_dict.pop("event"),
            "time": event_dict.pop("timestamp"),
        }

        event_dict[CLOUD_LOGGING_KEY] = value
        return event_dict


class FormatAsCloudLogging:
    """Finalize the Google Cloud Logging event message and replace the logging event"""

    def setup(self):
        return [
            self.__call__,
            structlog.processors.JSONRenderer(),
        ]

    def __call__(self, logger, method_name, event_dict):
        event = event_dict.pop(CLOUD_LOGGING_KEY)

        if event_dict:
            event["logging.googleapis.com/labels"] = event_dict

        return event


class LogSeverity:
    """Set the severity using the Google Cloud Logging severities"""

    def __init__(self):
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

    def setup(self):
        return [
            # Add log level to event dict.
            structlog.processors.add_log_level,
            self.__call__,
        ]

    def __call__(self, logger, method_name, event_dict):
        """Format a Python log level value as a GCP log severity.

        See: https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity
        """

        log_level = event_dict.pop("level")
        severity = self.mapping.get(log_level, self.default)

        event_dict[CLOUD_LOGGING_KEY]["severity"] = severity
        return event_dict


class CodeLocation:
    """Inject the location of the logging message into the logs"""

    def setup(self):
        # Add callsite parameters.
        call_site_proc = structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        )
        return [call_site_proc, self.__call__]

    def __call__(self, logger, method_name, event_dict):
        location = {
            "file": event_dict.pop("pathname"),
            "line": str(event_dict.pop("lineno")),
            "function": f"{event_dict.pop('module')}:{event_dict.pop('func_name')}",
        }

        event_dict[CLOUD_LOGGING_KEY][SOURCE_LOCATION_KEY] = location

        return event_dict
