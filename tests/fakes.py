"""Fake implementations of structlog processors with side-effects"""

from typing import Collection

from structlog.processors import CallsiteParameter
from structlog.typing import EventDict, WrappedLogger


class CallsiteParameterAdder:
    def __init__(self, parameters: Collection[CallsiteParameter]) -> None:
        pass

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        event_dict["pathname"] = "/app/test.py"
        event_dict["lineno"] = 42
        event_dict["module"] = "test"
        event_dict["func_name"] = "test123"
        return event_dict


class TimeStamper:
    def __init__(self, fmt: str) -> None:
        pass

    def __call__(
        self, logger: WrappedLogger, method_name: str, event_dict: EventDict
    ) -> EventDict:
        event_dict["timestamp"] = "2023-04-01T08:00:00.000000Z"
        return event_dict


def format_exc_info(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        event_dict["exception"] = "Traceback blabla"
    return event_dict
