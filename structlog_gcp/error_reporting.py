import os

import structlog.processors
from structlog.typing import EventDict, Processor, WrappedLogger

from .constants import CLOUD_LOGGING_KEY, ERROR_EVENT_TYPE, SOURCE_LOCATION_KEY


def setup_exceptions() -> list[Processor]:
    return [structlog.processors.format_exc_info, ReportException()]


class ReportException:
    """Transform exception into a Google Cloud Error Reporting event."""

    # https://cloud.google.com/error-reporting/reference/rest/v1beta1/projects.events/report
    # https://cloud.google.com/error-reporting/docs/formatting-error-messages#log-entry-examples

    def __init__(self) -> None:
        pass

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        exception = event_dict.pop("exception", None)
        if exception is None:
            return event_dict

        event_dict[CLOUD_LOGGING_KEY]["@type"] = ERROR_EVENT_TYPE

        # https://cloud.google.com/error-reporting/docs/formatting-error-messages
        message = event_dict[CLOUD_LOGGING_KEY]["message"]
        error_message = f"{message}\n{exception}"
        event_dict[CLOUD_LOGGING_KEY]["stack_trace"] = error_message

        return event_dict


class ReportError:
    """Report to Google Cloud Error Reporting specific log severities

    This class assumes the :ref:`.processors.CodeLocation` processor ran before.
    """

    # https://cloud.google.com/error-reporting/reference/rest/v1beta1/projects.events/report
    # https://cloud.google.com/error-reporting/docs/formatting-error-messages#log-entry-examples

    def __init__(self, severities: list[str]) -> None:
        self.severities = severities

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        severity = event_dict[CLOUD_LOGGING_KEY]["severity"]
        has_strack_trace = "stack_trace" in event_dict[CLOUD_LOGGING_KEY]

        if severity not in self.severities and not has_strack_trace:
            return event_dict

        # https://cloud.google.com/error-reporting/reference/rest/v1beta1/ErrorContext
        error_context = {
            "reportLocation": event_dict[CLOUD_LOGGING_KEY][SOURCE_LOCATION_KEY],
        }

        event_dict[CLOUD_LOGGING_KEY]["@type"] = ERROR_EVENT_TYPE
        event_dict[CLOUD_LOGGING_KEY]["context"] = error_context

        # "serviceContext" should be added by the ServiceContext processor.
        # event_dict[CLOUD_LOGGING_KEY]["serviceContext"]

        return event_dict


class ServiceContext:
    def __init__(self, service: str | None = None, version: str | None = None) -> None:
        # https://cloud.google.com/functions/docs/configuring/env-var#runtime_environment_variables_set_automatically
        if service is None:
            service = os.environ.get("K_SERVICE", "unknown service")

        if version is None:
            version = os.environ.get("K_REVISION", "unknown version")

        self.service_context = {"service": service, "version": version}

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        """Add a service context in which an error has occurred.

        This is part of the Error Reporting API, so it's only added when an error happens.
        """

        event_type = event_dict[CLOUD_LOGGING_KEY].get("@type")
        if event_type != ERROR_EVENT_TYPE:
            return event_dict

        # https://cloud.google.com/error-reporting/reference/rest/v1beta1/ServiceContext
        event_dict[CLOUD_LOGGING_KEY]["serviceContext"] = self.service_context

        return event_dict
