"""Base class for checks.

To add a check: subclass `Check`, implement `run`, and register an instance in
`vigilo.checks.ALL_CHECKS`. Keep the network I/O thin and put the decision logic in
pure functions so it can be unit-tested without the network.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

import httpx

from vigilo.models import Finding
from vigilo.target import Target


@dataclass(frozen=True)
class ScanContext:
    target: Target
    http: httpx.AsyncClient
    allow_private: bool = False
    # The home page fetched once at the start of the scan, reused by checks so that each
    # resource is requested only once. None if it could not be fetched over HTTPS.
    homepage: httpx.Response | None = None
    # Public addresses the target resolved to, validated once. Raw socket checks (TLS)
    # connect to these instead of resolving the name again. Empty in local testing mode.
    addresses: tuple[str, ...] = ()
    # The home page HTML, when it was served as HTML. Used by content checks.
    html: str = ""


class Check(ABC):
    name: ClassVar[str]
    label: ClassVar[str]  # shown to users while the scan runs
    description: ClassVar[str]

    @abstractmethod
    async def run(self, ctx: ScanContext) -> list[Finding]:
        """Run the check and return its findings."""
