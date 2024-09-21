from dataclasses import dataclass
from typing import Any

from structlog.typing import EventDict, WrappedLogger

from ..types import CLOUD_LOGGING_KEY

__all__ = ["HTTPRequest"]


@dataclass
class HTTPRequest:
    method: str | None = None
    """The request method.

    Examples: ``GET``, ``HEAD``, ``PUT``, ``POST``."""

    url: str | None = None
    """The scheme (``http``, ``https``), the host name, the path and the query portion of the URL that was requested.

    Example: ``http://example.com/some/info?color=red``
    """

    size: int | None = None
    "The size of the HTTP request message in bytes, including the request headers and the request body."

    status: int | None = None
    """The response code indicating the status of response.

    Examples: ``200``, ``404``."""

    response_size: int | None = None
    """The size of the HTTP response message sent back to the client, in bytes, including the response headers and the response body."""

    latency_ns: int | None = None
    """The request processing latency (in nanoseconds) on the server, from the time the request was received until the response was sent.

    For WebSocket connections, this field refers to the entire time duration of the connection."""

    protocol: str | None = None
    """Protocol used for the request.

    Examples: ``HTTP/1.1``, ``HTTP/2``."""

    referer: str | None = None
    "The referer URL of the request, as defined in `HTTP/1.1 Header Field Definitions <https://datatracker.ietf.org/doc/html/rfc2616#section-14.36>`_."

    user_agent: str | None = None
    """The user agent sent by the client.

    Example: ``Mozilla/4.0 (compatible; MSIE 6.0; Windows 98; Q312461; .NET CLR 1.0.3705)``."""

    remote_ip: str | None = None
    """The IP address (IPv4 or IPv6) of the client that issued the HTTP request. This field can include port information.

    Examples: ``192.168.1.1``, ``10.0.0.1:80``, ``FE80::0202:B3FF:FE1E:8329``."""

    server_ip: str | None = None
    """The IP address (IPv4 or IPv6) of the origin server that the request was sent to. This field can include port information.

    Examples: ``192.168.1.1``, ``10.0.0.1:80``, ``FE80::0202:B3FF:FE1E:8329``."""

    cache_lookup: bool | None = None
    "Whether or not a cache lookup was attempted."

    cache_hit: bool | None = None
    "Whether or not an entity was served from cache (with or without validation)."

    cache_validated_with_origin_server: bool | None = None
    """Whether or not the response was validated with the origin server before being served from cache.

    This field is only meaningful if ``cache_hit`` is ``True``."""

    cache_fill: int | None = None
    "The number of HTTP response bytes inserted into cache. Set only when a cache fill was attempted."

    def format(self) -> dict[str, Any]:
        """Format as https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry#httprequest"""

        values = [
            ("requestMethod", self.method),
            ("requestUrl", self.url),
            ("requestSize", str_or_none(self.size)),
            ("status", self.status),
            ("responseSize", str_or_none(self.response_size)),
            ("userAgent", self.user_agent),
            ("remoteIp", self.remote_ip),
            ("serverIp", self.server_ip),
            ("referer", self.referer),
            ("latency", seconds_or_none(self.latency_ns)),
            ("cacheLookup", self.cache_lookup),
            ("cacheHit", self.cache_hit),
            ("cacheValidatedWithOriginServer", self.cache_validated_with_origin_server),
            ("cacheFillBytes", str_or_none(self.cache_fill)),
            ("protocol", self.protocol),
        ]

        return {k: v for (k, v) in values if v is not None}


def request_processor(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    if "http_request" not in event_dict:
        return event_dict

    request: HTTPRequest = event_dict.pop("http_request")

    event_dict[CLOUD_LOGGING_KEY]["httpRequest"] = request.format()
    return event_dict


def str_or_none(value: int | None) -> str | None:
    """Convert a value to string, or ``None``.

    >>> str_or_none(None)
    >>> str_or_none(15)
    '15'
    """

    if value is None:
        return None

    return str(value)


def seconds_or_none(value_ns: int | None) -> str | None:
    """Convert a value in nanosecond to a duration in second, or ``None``.

    >>> ns = 1
    >>> us = ns * 1000
    >>> ms = us * 1000
    >>> s = ms * 1000
    >>> seconds_or_none(None)
    >>> seconds_or_none(1 * ns)
    '0.000000001s'
    >>> seconds_or_none(15 * ms)
    '0.015s'
    >>> seconds_or_none(1 * s)
    '1s'
    >>> seconds_or_none(99.5 * s)
    '99.5s'
    """

    if value_ns is None:
        return None

    seconds = value_ns / 1e9
    # Remove trailing 0 and . to keep number cleaner
    seconds_str = f"{seconds:.9f}".rstrip("0.")
    return f"{seconds_str}s"
