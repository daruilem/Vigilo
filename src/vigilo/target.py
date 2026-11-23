"""Target parsing and validation.

Vigilo is meant to run as a public web service, so it must never be usable to probe
internal networks (SSRF). Every hostname is resolved and rejected if any of its
addresses is not publicly routable.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

from vigilo.errors import ScanError

_LABEL = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)")


class TargetError(ScanError):
    """The target is malformed or not allowed."""

    code = "invalid_target"


@dataclass(frozen=True)
class Target:
    hostname: str
    port: int = 443

    @property
    def https_url(self) -> str:
        suffix = "" if self.port == 443 else f":{self.port}"
        return f"https://{self.hostname}{suffix}/"

    @property
    def http_url(self) -> str:
        return f"http://{self.hostname}/"


def parse_target(raw: str) -> Target:
    """Turn user input ('example.com', 'https://example.com/page') into a Target."""
    raw = raw.strip()
    if not raw:
        raise TargetError("Enter a website address, for example example.com.")
    if "://" not in raw:
        raw = "https://" + raw

    parts = urlsplit(raw)
    if parts.scheme not in ("http", "https"):
        raise TargetError("Only addresses starting with http:// or https:// can be checked.")
    if not parts.hostname:
        raise TargetError("This does not look like a website address. Use a form like example.com.")

    host = parts.hostname.rstrip(".").lower()
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise TargetError("Enter a domain name such as example.com, not an IP address.")

    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise TargetError(
            "This domain name is not valid. Check the spelling, for example example.com."
        ) from exc

    labels = host.split(".")
    if len(host) > 253 or len(labels) < 2 or not all(_LABEL.fullmatch(lb) for lb in labels):
        raise TargetError(
            "This domain name is not valid. Check the spelling, for example example.com."
        )

    try:
        port = parts.port or 443
    except ValueError as exc:
        raise TargetError(
            "The port number in the address is not valid. Remove it and try again."
        ) from exc

    return Target(hostname=host, port=port)


def is_public_address(address: str) -> bool:
    """True if the IP address is globally routable (not private, loopback, link-local...)."""
    ip = ipaddress.ip_address(address.split("%", 1)[0])
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


async def ensure_public_host(hostname: str) -> list[str]:
    """Resolve `hostname` and fail unless every address is public. Returns the addresses."""
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise TargetError(
            f"The domain '{hostname}' does not exist. Check the spelling of the address.",
            code="dns_error",
        ) from exc

    addresses = sorted({str(info[4][0]) for info in infos})
    if not addresses:
        raise TargetError(
            f"The domain '{hostname}' does not exist. Check the spelling of the address.",
            code="dns_error",
        )
    if not all(is_public_address(a) for a in addresses):
        raise TargetError(
            f"The domain '{hostname}' points to a private network, which Vigilo does not check.",
            code="forbidden_target",
        )
    return addresses
