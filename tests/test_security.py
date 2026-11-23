import asyncio

import httpx
import pytest

from vigilo.clientip import client_ip, parse_networks
from vigilo.net import PublicOnlyBackend, fetch_page
from vigilo.target import TargetError

PROXIES = parse_networks("127.0.0.1, 10.0.0.0/8")


@pytest.mark.parametrize(
    ("peer", "forwarded", "expected"),
    [
        ("203.0.113.5", "1.1.1.1", "203.0.113.5"),  # peer is not a proxy: header ignored
        ("127.0.0.1", None, "127.0.0.1"),
        ("127.0.0.1", "198.51.100.7", "198.51.100.7"),
        ("127.0.0.1", "6.6.6.6, 198.51.100.7", "198.51.100.7"),  # forged left part ignored
        ("127.0.0.1", "198.51.100.7, 10.1.2.3", "198.51.100.7"),  # chain of trusted proxies
        ("127.0.0.1", "not-an-ip", "127.0.0.1"),
    ],
)
def test_client_ip(peer, forwarded, expected):
    assert client_ip(peer, forwarded, PROXIES) == expected


def test_client_ip_without_trusted_proxies_uses_the_peer():
    assert client_ip("127.0.0.1", "198.51.100.7", ()) == "127.0.0.1"


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "10.0.0.8", "169.254.169.254", "::1"])
def test_backend_refuses_private_addresses(host):
    async def go():
        await PublicOnlyBackend().connect_tcp(host, 80, timeout=1)

    with pytest.raises(TargetError):
        asyncio.run(go())


def test_backend_never_resolves_twice(monkeypatch):
    """The socket must be opened to the address that was checked, not to the name."""
    from vigilo import net

    connected = []

    async def fake_resolve(host):
        return ["93.184.215.14"]

    class Inner:
        async def connect_tcp(self, host, port, *args):
            connected.append(host)
            return object()

    monkeypatch.setattr(net, "ensure_public_host", fake_resolve)
    backend = PublicOnlyBackend()
    backend._inner = Inner()
    asyncio.run(backend.connect_tcp("example.com", 443))
    assert connected == ["93.184.215.14"]


def test_fetch_page_caps_the_body():
    def handler(request):
        return httpx.Response(200, content=b"x" * 5000, headers={"Content-Type": "text/html"})

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await fetch_page(http, "https://example.com/", max_bytes=1000)

    page = asyncio.run(go())
    assert page.status_code == 200
    assert len(page.content) == 1000
    assert page.headers["content-type"] == "text/html"


def test_fetch_page_keeps_non_ascii_headers():
    def handler(request):
        return httpx.Response(200, headers=[(b"X-Fun", "\u26c4 snow".encode())], content=b"ok")

    async def go():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await fetch_page(http, "https://example.com/")

    page = asyncio.run(go())
    assert page.headers.raw[0][1] == "\u26c4 snow".encode()
