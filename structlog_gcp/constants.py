ERROR_EVENT_TYPE = (
    "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent"
)

SOURCE_LOCATION_KEY = "logging.googleapis.com/sourceLocation"

CLOUD_LOGGING_KEY = "cloud-logging"

# From Python's logging level to Google level
# https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#LogSeverity
SEVERITY_MAPPING = {
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
