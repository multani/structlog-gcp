import json
from unittest.mock import patch

import structlog
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.types import ASGIApp
from structlog.typing import WrappedLogger

from structlog_gcp.http.adapters.starlette import RequestAdapter

from .conftest import T_stdout


class LoggerMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.logger = structlog.get_logger()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        mocked_scope = {}
        if "no-client" in str(request.url):
            # Remove the client information to test the adapter works correctly
            # when the client is not set.
            mocked_scope = {"client": None}

        async with RequestAdapter(request) as adapter:
            with patch.dict(request.scope, mocked_scope):
                response = await call_next(request)
                r = adapter.adapt(response)

        # We don't know how much time the call will take, and we can't assert
        # the latency value later on, so we fake it here to a static value.
        assert r.latency_ns is not None
        assert r.latency_ns > 0
        r.latency_ns = 42 * 1_000_000

        self.logger.info(
            f"{r.method} {r.url} {r.protocol} -> {r.status}",
            http_request=r,
        )

        return response


def index(request: Request) -> PlainTextResponse:
    return PlainTextResponse("ok")


def create_app() -> Starlette:
    middlewares = [Middleware(LoggerMiddleware)]
    routes = [Route("/", index)]
    return Starlette(routes=routes, middleware=middlewares)


async def test_basic(stdout: T_stdout, logger: WrappedLogger) -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/?foo=bar")
    assert response.status_code == 200

    expected = {
        "logging.googleapis.com/sourceLocation": {
            "file": "/app/test.py",
            "function": "test:test123",
            "line": "42",
        },
        "httpRequest": {
            "latency": "0.042s",
            "protocol": "HTTP/1.1",
            "remoteIp": "testclient:50000",
            "requestMethod": "GET",
            "requestUrl": "http://testserver/?foo=bar",
            "status": 200,
            "userAgent": "testclient",
        },
        "message": "GET http://testserver/?foo=bar HTTP/1.1 -> 200",
        "severity": "INFO",
        "time": "2023-04-01T08:00:00.000000Z",
    }

    msg = json.loads(stdout())
    assert msg == expected


async def test_no_remote_ip(stdout: T_stdout, logger: WrappedLogger) -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/?no-client")
    assert response.status_code == 200

    msg = json.loads(stdout())
    assert "remoteIp" not in msg["httpRequest"]
