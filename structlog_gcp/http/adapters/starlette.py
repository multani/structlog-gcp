import time
from types import TracebackType
from typing import (
    Self,
    Type,
)

from starlette.requests import Request
from starlette.responses import Response

from ..base import HTTPRequest


class RequestAdapter:
    def __init__(self, request: Request):
        self.request = request
        self.start_time = time.perf_counter_ns()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return None

    def adapt(self, response: Response) -> HTTPRequest:
        request = self.request  # alias

        latency_ns = time.perf_counter_ns() - self.start_time
        http_version = request.scope["http_version"]

        if request.client is not None:
            client_host = request.client.host
            client_port = request.client.port
            remote_ip = f"{client_host}:{client_port}"
        else:
            remote_ip = None

        return HTTPRequest(
            method=request.method,
            url=str(request.url),
            status=response.status_code,
            latency_ns=latency_ns,
            protocol=f"HTTP/{http_version}",
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
            remote_ip=remote_ip,
        )
