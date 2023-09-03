import datetime
import json
from unittest.mock import patch

import structlog

import structlog_gcp


def test_normal(stdout, logger):
    logger.info("test")

    msg = json.loads(stdout())

    expected = {
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "message": "test",
        "severity": "INFO",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert expected == msg


def test_error(stdout, logger):
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes", foo="bar")

    msg = json.loads(stdout())

    expected = {
        "@type": "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent",
        "context": {
            "reportLocation": {
                "file": "/app/test.py",
                "function": "test:test123",
                "line": "42",
            },
        },
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "serviceContext": {
            "service": "unknown service",
            "version": "unknown version",
        },
        "foo": "bar",
        "severity": "CRITICAL",
        "message": "oh noes",
        "stack_trace": "oh noes\nTraceback blabla",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert expected == msg


def test_service_context_default(stdout, logger):
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes")

    msg = json.loads(stdout())

    assert msg["serviceContext"] == {
        "service": "unknown service",
        "version": "unknown version",
    }


@patch.dict("os.environ", {"K_SERVICE": "test-service", "K_REVISION": "test-version"})
def test_service_context_envvar(stdout, mock_logger_env):
    processors = structlog_gcp.build_processors()
    structlog.configure(processors=processors)
    logger = structlog.get_logger()

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes")

    msg = json.loads(stdout())

    assert msg["serviceContext"] == {
        "service": "test-service",
        "version": "test-version",
    }


def test_service_context_custom(stdout, mock_logger_env):
    processors = structlog_gcp.build_processors(
        service="my-service",
        version="deadbeef",
    )
    structlog.configure(processors=processors)
    logger = structlog.get_logger()

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes")

    msg = json.loads(stdout())

    assert msg["serviceContext"] == {
        "service": "my-service",
        "version": "deadbeef",
    }


def test_extra_labels(stdout, logger):
    logger.info(
        "test",
        test1="test1",
        test2=2,
        test3=False,
        test4={"foo": "bar"},
        test5={"date": datetime.date(2023, 1, 1)},
    )

    msg = json.loads(stdout())

    expected = {
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "severity": "INFO",
        "time": "2023-04-01T08:00:00.000000Z",
        "message": "test",

        # This should be parsed automatically by Cloud Logging into dedicated keys and saved into a JSON payload.
        # See: https://cloud.google.com/logging/docs/structured-logging#special-payload-fields
        "test1": "test1",
        "test2": 2,
        "test3": False,
        "test4": {"foo": "bar"},
        "test5": {"date": "datetime.date(2023, 1, 1)"},
    }
    assert expected == msg
