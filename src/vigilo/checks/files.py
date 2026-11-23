"""Sensitive files check.

Looks for files that should never be public: Git metadata, environment files and
backups. Ethics rule: only the status code, the declared size and the content type are
looked at. The response body is never read, displayed or stored.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from vigilo.checks.base import Check, ScanContext
from vigilo.models import Finding, Observation, Severity, Status

CHECK = "files"
MAX_CONCURRENCY = 3
NOT_READ_NOTE = "Status code and size only. The file was not read, shown or stored."


@dataclass(frozen=True)
class Group:
    id: str
    title: str
    severity: Severity
    description: str
    paths: tuple[str, ...]


GROUPS: tuple[Group, ...] = (
    Group(
        id="files.git",
        title="Git repository metadata",
        severity=Severity.HIGH,
        description=(
            "The .git folder holds the full history of the site's code, which often "
            "includes passwords and private settings. Anyone can download it."
        ),
        paths=("/.git/HEAD", "/.git/config"),
    ),
    Group(
        id="files.env",
        title="Environment file",
        severity=Severity.CRITICAL,
        description=(
            "The .env file usually holds database passwords and secret keys. Anyone who "
            "downloads it can take control of the site or its data."
        ),
        paths=("/.env",),
    ),
    Group(
        id="files.backup",
        title="Backup files",
        severity=Severity.HIGH,
        description=(
            "Backups in the public folder can contain the whole database, including "
            "customer data and password hashes."
        ),
        paths=("/backup.zip", "/backup.sql", "/database.sql", "/dump.sql", "/wp-config.php.bak"),
    ),
)


@dataclass(frozen=True)
class Probe:
    path: str
    status: int
    size: int | None
    content_type: str


class FilesCheck(Check):
    name = CHECK
    label = "Sensitive files (status and size only)"
    description = "Looks for Git metadata, environment files and backups left in public."

    async def run(self, ctx: ScanContext) -> list[Finding]:
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        base = ctx.target.https_url.rstrip("/")

        async def probe(path: str) -> Probe | None:
            async with semaphore:
                try:
                    return await probe_path(ctx.http, base + path, path)
                except httpx.HTTPError:
                    return None

        paths = [p for group in GROUPS for p in group.paths]
        results = await asyncio.gather(*(probe(p) for p in paths))
        probes = [r for r in results if r is not None]
        if not probes:
            raise RuntimeError("no sensitive path could be checked")
        return evaluate_probes(probes)


async def probe_path(http: httpx.AsyncClient, url: str, path: str) -> Probe:
    # Streaming without reading: the body is never downloaded into memory or stored.
    async with http.stream("GET", url, follow_redirects=False) as response:
        length = response.headers.get("content-length", "")
        return Probe(
            path=path,
            status=response.status_code,
            size=int(length) if length.isdigit() else None,
            content_type=response.headers.get("content-type", "").lower(),
        )


def is_exposed(probe: Probe) -> bool:
    """A file counts as exposed only if it is served as-is.

    Many sites answer 200 with an HTML "not found" page for any address, so an HTML
    response is not counted, nor is an empty one.
    """
    if probe.status != 200:
        return False
    if probe.content_type.startswith(("text/html", "application/xhtml")):
        return False
    return probe.size != 0


def describe(probe: Probe) -> str:
    size = "size unknown" if probe.size is None else f"{probe.size:,} bytes".replace(",", " ")
    return f"{probe.status} OK · {size}"


def evaluate_probes(probes: list[Probe]) -> list[Finding]:
    by_path = {p.path: p for p in probes}
    findings: list[Finding] = []
    for group in GROUPS:
        exposed = [by_path[p] for p in group.paths if p in by_path and is_exposed(by_path[p])]
        if exposed:
            findings.append(
                Finding(
                    id=group.id,
                    check=CHECK,
                    title=group.title,
                    status=Status.FAIL,
                    severity=group.severity,
                    description=group.description,
                    observed=[
                        Observation(label=f"GET {p.path}", value=describe(p)) for p in exposed
                    ],
                    note=NOT_READ_NOTE,
                    evidence={"exposed": [p.path for p in exposed]},
                )
            )

    if not findings:
        findings.append(
            Finding(
                id="files.none",
                check=CHECK,
                title="Sensitive files",
                status=Status.PASS,
                description="No Git metadata, environment file or common backup is served.",
                observed=[
                    Observation(
                        label=f"{len(probes)} paths checked",
                        value="none served",
                    )
                ],
                note=NOT_READ_NOTE,
            )
        )
    return findings
