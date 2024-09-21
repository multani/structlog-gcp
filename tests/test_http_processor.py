import json

from structlog.typing import WrappedLogger

from structlog_gcp.http.base import HTTPRequest

from .conftest import T_stdout


def test_http_1() -> None:
    request = HTTPRequest(method="GET", status=200, size=512)
    result = request.format()

    expected = {
        "requestMethod": "GET",
        "status": 200,
        "requestSize": "512",
    }

    assert result == expected


def test_http_latency() -> None:
    request = HTTPRequest(method="GET", latency_ns=15_000_000)
    result = request.format()

    expected = {
        "requestMethod": "GET",
        "latency": "0.015s",
    }

    assert result == expected


def test_http_logger(stdout: T_stdout, logger: WrappedLogger) -> None:
    request = HTTPRequest(method="GET", status=200)

    logger.info("test", http_request=request)

    msg = json.loads(stdout())

    expected = {
        "httpRequest": {
            "requestMethod": "GET",
            "status": 200,
        },
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
