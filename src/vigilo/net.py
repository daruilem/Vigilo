"""Shared HTTP client, hardened against server-side request forgery (SSRF).

Every outgoing connection, including each redirect hop, goes through `PublicOnlyBackend`:
the host name is resolved once, every address is checked to be public, and the socket
is opened to exactly that checked address. Because the name is never resolved a second
time, a DNS answer that changes between the check and the connection (DNS rebinding)
cannot redirect Vigilo to an internal service.
"""

from __future__ import annotations

import typing

import httpcore
import httpx

from vigilo import __version__
from vigilo.target import ensure_public_host

USER_AGENT = f"Vigilo/{__version__} (website security check-up; passive checks)"
DEFAULT_TIMEOUT = httpx.Timeout(10.0)
MAX_REDIRECTS = 5
MAX_CONNECTIONS = 10


class PublicOnlyBackend(httpcore.AsyncNetworkBackend):
    def __init__(self) -> None:
        self._inner = httpcore.AnyIOBackend()

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: typing.Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.AsyncNetworkStream:
        addresses = await ensure_public_host(host)
        last_error: Exception | None = None
        for address in addresses:
            try:
                # TLS still uses the original host name for SNI and certificate checks:
                # httpcore takes it from the request, not from this socket address.
                return await self._inner.connect_tcp(
                    address, port, timeout, local_address, socket_options
                )
            except httpcore.ConnectError as exc:
                last_error = exc
        assert last_error is not None
        raise last_error

    async def connect_unix_socket(
        self,
        path: str,
        timeout: float | None = None,
        socket_options: typing.Iterable[httpcore.SOCKET_OPTION] | None = None,
    ) -> httpcore.AsyncNetworkStream:
        raise httpcore.ConnectError("Unix sockets are not allowed.")

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


class PublicOnlyTransport(httpx.AsyncHTTPTransport):
    """httpx transport whose connections can only reach public addresses.

    Environment proxies are ignored on purpose: a proxy would make the address check
    meaningless.
    """

    def __init__(self) -> None:
        super().__init__(trust_env=False)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=httpx.create_ssl_context(trust_env=False),
            max_connections=MAX_CONNECTIONS,
            network_backend=PublicOnlyBackend(),
        )


MAX_PAGE_BYTES = 2_000_000


async def fetch_page(
    http: httpx.AsyncClient, url: str, max_bytes: int = MAX_PAGE_BYTES
) -> httpx.Response:
    """GET a page, following redirects, but never keep more than `max_bytes` of body.

    A hostile server could otherwise send an endless response and exhaust memory.
    """
    async with http.stream("GET", url) as response:
        chunks: list[bytes] = []
        size = 0
        async for chunk in response.aiter_bytes():
            chunks.append(chunk)
            size += len(chunk)
            if size >= max_bytes:
                break
    # The body is already decoded, so the encoding headers no longer describe it.
    # Raw bytes: servers sometimes send non-ASCII header values, which must not crash us.
    headers = [
        (k, v)
        for k, v in response.headers.raw
        if k.lower() not in (b"content-encoding", b"content-length", b"transfer-encoding")
    ]
    return httpx.Response(
        response.status_code,
        headers=headers,
        content=b"".join(chunks)[:max_bytes],
        request=response.request,
    )


def make_client(
    *, allow_private: bool = False, transport: httpx.AsyncBaseTransport | None = None
) -> httpx.AsyncClient:
    if transport is None and not allow_private:
        transport = PublicOnlyTransport()
    return httpx.AsyncClient(
        headers={"User-Agent": USER_AGENT},
        timeout=DEFAULT_TIMEOUT,
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
        transport=transport,
        trust_env=False,
    )
