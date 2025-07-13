import datetime
from unittest.mock import patch

import structlog
from _pytest.capture import CaptureFixture
from structlog.typing import WrappedLogger

import structlog_gcp

from .conftest import T_stdout


def test_normal(stdout: T_stdout, logger: WrappedLogger) -> None:
    logger.info("test")

    msg = next(stdout)

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
    assert msg == expected


def test_exception(stdout: T_stdout, logger: WrappedLogger) -> None:
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes", foo="bar")

    msg = next(stdout)

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
        "severity": "ERROR",
        "message": "oh noes",
        "stack_trace": "Traceback (most recent call last):\n...\nZeroDivisionError: division by zero",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert msg == expected


def test_service_context_default(stdout: T_stdout, logger: WrappedLogger) -> None:
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes")

    msg = next(stdout)

    assert msg["serviceContext"] == {
        "service": "unknown service",
        "version": "unknown version",
    }


@patch.dict("os.environ", {"K_SERVICE": "test-service", "K_REVISION": "test-version"})
def test_service_context_envvar(stdout: T_stdout, mock_logger_env: None) -> None:
    processors = structlog_gcp.build_processors()
    structlog.configure(processors=processors)
    logger = structlog.get_logger()

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oh noes")

    msg = next(stdout)

    assert msg["serviceContext"] == {
        "service": "test-service",
        "version": "test-version",
    }


def test_service_context_custom(stdout: T_stdout, mock_logger_env: None) -> None:
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

    msg = next(stdout)

    assert msg["serviceContext"] == {
        "service": "my-service",
        "version": "deadbeef",
    }


def test_extra_labels(stdout: T_stdout, logger: WrappedLogger) -> None:
    logger.info(
        "test",
        test1="test1",
        test2=2,
        test3=False,
        test4={"foo": "bar"},
        test5={"date": datetime.date(2023, 1, 1)},
    )

    msg = next(stdout)

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
    assert msg == expected


def test_contextvars_supported(stdout: T_stdout, logger: WrappedLogger) -> None:
    structlog.contextvars.bind_contextvars(
        request_id="1234",
    )

    logger.info("test")
    msg = next(stdout)

    expected = {
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "message": "test",
        "request_id": "1234",
        "severity": "INFO",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert msg == expected


def test_core_processors_only(
    capsys: CaptureFixture[str], mock_logger_env: None
) -> None:
    processors = structlog_gcp.build_gcp_processors()
    processors.append(structlog.processors.KeyValueRenderer())

    structlog.configure(processors=processors)
    logger = structlog.get_logger()

    # This will not be logged as the contextvars processor is not configured in the "core" processors.
    structlog.contextvars.bind_contextvars(
        request_id="1234",
    )

    logger.info("test")

    output = capsys.readouterr()
    assert "" == output.err
    msg = output.out.strip()

    # No JSON formatting, no contextvars
    expected = "message='test' time='2023-04-01T08:00:00.000000Z' severity='INFO' logging.googleapis.com/sourceLocation={'file': '/app/test.py', 'line': '42', 'function': 'test:test123'}"

    assert expected == msg


def test_exception_different_level(stdout: T_stdout, logger: WrappedLogger) -> None:
    try:
        1 / 0
    except ZeroDivisionError as exc:
        logger.warning("oh no; anyways", exception=exc)

    msg = next(stdout)

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
        "severity": "WARNING",
        "message": "oh no; anyways",
        "stack_trace": "ZeroDivisionError('division by zero')",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert msg == expected


def test_exception_handled(stdout: T_stdout, logger: WrappedLogger) -> None:
    try:
        1 / 0
    except ZeroDivisionError as exc:
        logger.info(f"I was expecting that error: {exc}")

    msg = next(stdout)

    expected = {
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "severity": "INFO",
        "message": "I was expecting that error: division by zero",
        "time": "2023-04-01T08:00:00.000000Z",
    }
    assert msg == expected
