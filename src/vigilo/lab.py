"""Local lab mode: test the active scan against deliberately vulnerable apps on your machine.

Vigilo normally refuses private addresses (SSRF protection). A lab lists the few hosts it
may reach anyway, for example OWASP Juice Shop started by `docker-compose.lab.yml`:

    VIGILO_LAB_TARGETS="juice.lab=http://127.0.0.1:8080"

Each entry maps a lab host name to the address where the API process can reach it.
Scanning containers reach the same app by its host name on the lab's Docker network
(`VIGILO_LAB_NETWORK`, default `vigilo-lab`).

Two rules keep this from ever touching a real website:
- lab host names must end in `.lab` or `.test`. `.test` is reserved by RFC 2606 and `.lab`
  is not delegated, so neither can be a real internet domain;
- the address must be a loopback or private address.

Never set VIGILO_LAB_TARGETS on a public server.
"""

from __future__ import annotations

import ipaddress
import logging
import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

LAB_SUFFIXES = (".lab", ".test")
DEFAULT_NETWORK = "vigilo-lab"


class LabConfigError(ValueError):
    """VIGILO_LAB_TARGETS is malformed or names something that is not a lab."""


@dataclass(frozen=True)
class LabTarget:
    host: str
    base_url: str  # how the API process reaches the app, without a trailing slash
    network: str  # Docker network the scanning containers join

    @property
    def scan_url(self) -> str:
        """How the scanning containers reach the app (by name, on the lab network)."""
        return f"http://{self.host}/"


def _private_address(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private


def parse_lab_targets(raw: str, network: str = DEFAULT_NETWORK) -> dict[str, LabTarget]:
    targets: dict[str, LabTarget] = {}
    for entry in filter(None, (part.strip() for part in raw.split(","))):
        host, sep, url = entry.partition("=")
        host = host.strip().lower().rstrip(".")
        url = url.strip().rstrip("/")
        if not sep or not host or not url:
            raise LabConfigError(f"Expected host=url, got {entry!r}.")
        if not host.endswith(LAB_SUFFIXES) or host in LAB_SUFFIXES:
            raise LabConfigError(f"Lab host {host!r} must end in .lab or .test.")
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise LabConfigError(f"Lab address {url!r} must be an http(s) URL.")
        if not _private_address(parts.hostname):
            raise LabConfigError(f"Lab address {url!r} must be a loopback or private address.")
        targets[host] = LabTarget(host=host, base_url=url, network=network)
    return targets


def load(env: Mapping[str, str] = os.environ) -> dict[str, LabTarget]:
    targets = parse_lab_targets(
        env.get("VIGILO_LAB_TARGETS", ""), env.get("VIGILO_LAB_NETWORK", DEFAULT_NETWORK)
    )
    if targets:
        logger.warning(
            "LAB MODE: Vigilo may reach %s. Never enable this on a public server.",
            ", ".join(sorted(targets)),
        )
    return targets
