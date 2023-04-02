"""Fake implementations of structlog processors with side-effects"""


class CallsiteParameterAdder:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, logger, method_name, event_dict):
        event_dict["pathname"] = "/app/test.py"
        event_dict["lineno"] = 42
        event_dict["module"] = "test"
        event_dict["func_name"] = "test123"
        return event_dict


class TimeStamper:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, logger, method_name, event_dict):
        event_dict["timestamp"] = "2023-04-01T08:00:00.000000Z"
        return event_dict


def format_exc_info(logger, method_name, event_dict):
    exc_info = event_dict.pop("exc_info", None)
    if exc_info:
        event_dict["exception"] = "Traceback blabla"
    return event_dict
