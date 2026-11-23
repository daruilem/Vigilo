"""Find the real client IP behind trusted reverse proxies.

`X-Forwarded-For` is set by the client and can be forged. It is only believed when the
direct peer is a proxy we trust, and then read from right to left: the first address
that is not a trusted proxy is the client. Without configured proxies, the direct peer
address is used.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterable

Network = ipaddress.IPv4Network | ipaddress.IPv6Network


def parse_networks(value: str) -> tuple[Network, ...]:
    """Parse a comma-separated list of IPs or CIDR ranges, e.g. '127.0.0.1,10.0.0.0/8'."""
    networks = []
    for part in value.split(","):
        part = part.strip()
        if part:
            networks.append(ipaddress.ip_network(part, strict=False))
    return tuple(networks)


def _parse_ip(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def _trusted(address: str, proxies: Iterable[Network]) -> bool:
    ip = _parse_ip(address)
    return ip is not None and any(ip in network for network in proxies)


def client_ip(peer: str, forwarded_for: str | None, proxies: tuple[Network, ...]) -> str:
    if not proxies or not forwarded_for or not _trusted(peer, proxies):
        return peer
    hops = [hop.strip() for hop in forwarded_for.split(",") if hop.strip()]
    for hop in reversed(hops):
        if _parse_ip(hop) is None:
            return peer  # malformed header: do not guess
        if not _trusted(hop, proxies):
            return hop
    return hops[0] if hops else peer
