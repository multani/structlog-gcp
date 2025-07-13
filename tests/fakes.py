"""Fake implementations of structlog processors with side-effects"""

from typing import Collection

from structlog._frames import _format_exception
from structlog.processors import CallsiteParameter, _figure_out_exc_info
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
    exc_info = _figure_out_exc_info(event_dict.pop("exc_info", None))

    if exc_info:
        exception = _format_exception(exc_info)
        # Format the exception, but only keep the "Traceback ..." and the
        # actual exception line, and skip all the rest.
        # We need to skip the middle lines as they contain the path to the
        # files, which differs depending on which path the library is tested
        # from.
        head = exception.splitlines()[0]
        tail = exception.splitlines()[-1]
        event_dict["exception"] = f"{head}\n...\n{tail}"
    return event_dict
