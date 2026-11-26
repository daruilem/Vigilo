"""Run the scanning tools in throwaway, locked-down Docker containers.

Each tool runs in its own container, started for one scan and removed afterwards:
- read-only file system, writable scratch space in memory only (tmpfs),
- every Linux capability dropped, no privilege escalation,
- memory, CPU and process limits, and a hard time limit (the container is killed),
- no volume from the host except the Nuclei templates, mounted read-only.

Scope. Outside the lab, the container's DNS is disabled and the verified host name is
pinned to the address Vigilo validated (`--add-host`). The tools can therefore only reach
that one site by name: a redirect to another host name fails to resolve. Direct IP
addresses remain reachable at the network level, so a production deployment must also
block private ranges for the scanning network with a firewall (see README).

Only "safe" checks run: no denial of service, no brute force, no fuzzing, no exploitation,
and no out-of-band callbacks to third-party servers (`-no-interactsh`).

The output is read from the container's standard output, capped in size, and handed to
`vigilo.active.parsers`, which keeps no data from the site.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import secrets
import shlex
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, field

import httpx

from vigilo import __version__

logger = logging.getLogger(__name__)

DOCKER = os.environ.get("VIGILO_DOCKER", "docker")
NUCLEI_IMAGE = os.environ.get("VIGILO_NUCLEI_IMAGE", "projectdiscovery/nuclei:latest")
ZAP_IMAGE = os.environ.get("VIGILO_ZAP_IMAGE", "ghcr.io/zaproxy/zaproxy:stable")
TEMPLATES_VOLUME = os.environ.get("VIGILO_NUCLEI_TEMPLATES_VOLUME", "vigilo-nuclei-templates")
SCAN_NETWORK = os.environ.get("VIGILO_SCAN_NETWORK", "bridge")

USER_AGENT = f"Vigilo-ActiveScan/{__version__} (verified owner)"
ZAP_USER_AGENT = f"Vigilo-ActiveScan/{__version__}"  # no spaces: ZAP splits -z on them
MAX_OUTPUT_BYTES = 10_000_000
ZAP_REPORT_MARKER = "=====VIGILO-ZAP-REPORT====="

# Nuclei tags that send heavy, risky or intrusive traffic: never run.
NUCLEI_EXCLUDED_TAGS = (
    "dos",
    "intrusive",
    "fuzz",
    "fuzzing",
    "bruteforce",
    "brute-force",
    "default-login",
    "rce",
    "sqli",
    "oast",
    "headless",
)


@dataclass(frozen=True)
class Limits:
    memory: str
    cpus: str
    pids: int = 256
    seconds: int = 600


NUCLEI_LIMITS = Limits(memory="1536m", cpus="1", seconds=600)
ZAP_LIMITS = Limits(memory="2g", cpus="1.5", pids=512, seconds=720)


@dataclass(frozen=True)
class ScanPlan:
    """Where and how the tools reach the verified site."""

    domain: str
    target_url: str
    network: str = SCAN_NETWORK
    # Outside the lab: the validated public address the host name is pinned to.
    pinned_address: str | None = None
    tools: tuple[str, ...] = ("nuclei", "zap")


@dataclass(frozen=True)
class ToolRun:
    tool: str
    argv: list[str]
    limits: Limits
    container: str = field(default="")


def _container_name(tool: str) -> str:
    return f"vigilo-{tool}-{secrets.token_hex(6)}"


def _base(plan: ScanPlan, name: str, limits: Limits) -> list[str]:
    argv = [
        DOCKER,
        "run",
        "--rm",
        "--name",
        name,
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        limits.memory,
        "--memory-swap",
        limits.memory,
        "--cpus",
        limits.cpus,
        "--pids-limit",
        str(limits.pids),
        "--network",
        plan.network,
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=256m",  # noqa: S108 - in-memory /tmp inside the container
    ]
    if plan.pinned_address:
        # No DNS at all: only the pinned host name resolves.
        argv += ["--dns", "0.0.0.0", "--add-host", f"{plan.domain}:{plan.pinned_address}"]  # noqa: S104 - DNS server that answers nothing
    return argv


def nuclei_run(plan: ScanPlan) -> ToolRun:
    name = _container_name("nuclei")
    argv = [
        *_base(plan, name, NUCLEI_LIMITS),
        "--tmpfs",
        "/root:rw,nosuid,size=64m",
        "--mount",
        f"type=volume,source={TEMPLATES_VOLUME},target=/templates,readonly",
        NUCLEI_IMAGE,
        "-target",
        plan.target_url,
        "-templates",
        "/templates/http",  # web checks only: network and cloud templates do not apply
        "-severity",
        "low,medium,high,critical",
        "-exclude-tags",
        ",".join(NUCLEI_EXCLUDED_TAGS),
        "-header",
        f"User-Agent: {USER_AGENT}",
        "-rate-limit",
        "20",
        "-concurrency",
        "10",
        "-bulk-size",
        "10",
        "-timeout",
        "10",
        "-retries",
        "0",
        "-no-interactsh",
        "-disable-update-check",
        "-jsonl",
        "-silent",
        "-no-color",
    ]
    return ToolRun("nuclei", argv, NUCLEI_LIMITS, name)


def zap_run(plan: ScanPlan) -> ToolRun:
    """ZAP baseline: spider for a short time and passive rules only, no attacks."""
    name = _container_name("zap")
    # The host name is validated, but this string goes through a shell: quote it anyway.
    baseline = (
        f"zap-baseline.py -t {shlex.quote(plan.target_url)} -m 2 -T 10 -I -J report.json "
        f"-z {shlex.quote('-config connection.defaultUserAgent=' + ZAP_USER_AGENT)} >&2; "
        f"echo {ZAP_REPORT_MARKER}; cat /zap/wrk/report.json"
    )
    argv = [
        *_base(plan, name, ZAP_LIMITS),
        "--tmpfs",
        "/zap/wrk:rw,nosuid,size=64m,mode=1777",
        "--tmpfs",
        "/home/zap:rw,nosuid,size=512m,mode=1777",
        ZAP_IMAGE,
        "sh",
        "-c",
        baseline,
    ]
    return ToolRun("zap", argv, ZAP_LIMITS, name)


TEMPLATES_VERSION = os.environ.get("VIGILO_NUCLEI_TEMPLATES_VERSION", "v10.5.2")
TEMPLATES_URL = (
    "https://github.com/projectdiscovery/nuclei-templates/archive/refs/tags/{version}.tar.gz"
)
MAX_TEMPLATES_BYTES = 100_000_000


def load_templates_argv() -> list[str]:
    """Unpack a templates archive read on standard input into the templates volume.

    The archive is downloaded by Vigilo itself (pinned version, see prepare_templates):
    Nuclei's own updater gives up on slow connections. This container has no network.
    """
    return [
        DOCKER,
        "run",
        "-i",
        "--rm",
        "--network",
        "none",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--memory",
        "256m",
        "--mount",
        f"type=volume,source={TEMPLATES_VOLUME},target=/templates",
        "--entrypoint",
        "sh",
        NUCLEI_IMAGE,
        "-c",
        "rm -rf /templates/* && tar -xzo -C /templates --strip-components=1 "
        "&& find /templates -name '*.yaml' | wc -l",
    ]


async def prepare_templates(version: str = TEMPLATES_VERSION) -> int:
    """Download the pinned Nuclei templates and install them. Returns the template count."""
    url = TEMPLATES_URL.format(version=version)
    timeout = httpx.Timeout(30.0, read=300.0)
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as http:
        response = await http.get(url)
        response.raise_for_status()
    if len(response.content) > MAX_TEMPLATES_BYTES:
        raise ToolFailed("nuclei", "templates archive too large")
    process = await asyncio.create_subprocess_exec(
        *load_templates_argv(),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, err = await process.communicate(response.content)
    if process.returncode != 0:
        raise ToolFailed("nuclei", err.decode("utf-8", "replace")[-300:] or "could not unpack")
    return int(out.decode().strip().splitlines()[-1])


def zap_report(stdout: str) -> str:
    """The JSON report printed after the marker, or an empty string."""
    _, sep, report = stdout.partition(ZAP_REPORT_MARKER)
    return report.strip() if sep else ""


# --- Execution ---------------------------------------------------------------------------


class ToolFailed(Exception):
    def __init__(self, tool: str, reason: str) -> None:
        super().__init__(f"{tool}: {reason}")
        self.tool = tool
        self.reason = reason


Runner = Callable[[ToolRun], Awaitable[str]]


async def _read_capped(stream: asyncio.StreamReader | None, limit: int) -> bytes:
    if stream is None:
        return b""
    data = bytearray()
    while chunk := await stream.read(65536):
        if len(data) < limit:
            data += chunk[: limit - len(data)]
    return bytes(data)


async def docker_runner(run: ToolRun) -> str:
    """Run one tool container and return its standard output (capped)."""
    process = await asyncio.create_subprocess_exec(
        *run.argv,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await _collect(process, run.limits.seconds)
    except asyncio.TimeoutError:
        await _stop(process, run.container)
        raise ToolFailed(run.tool, "time limit reached") from None
    except asyncio.CancelledError:
        await _stop(process, run.container)
        raise
    if process.returncode not in (0, None):
        tail = stderr.decode("utf-8", "replace")[-500:]
        logger.warning("%s exited with %s: %s", run.tool, process.returncode, tail)
        if not stdout.strip():
            raise ToolFailed(run.tool, f"exit code {process.returncode}")
    return stdout.decode("utf-8", "replace")


async def _collect(process: asyncio.subprocess.Process, seconds: int) -> tuple[bytes, bytes]:
    out, err, _ = await asyncio.wait_for(
        asyncio.gather(
            _read_capped(process.stdout, MAX_OUTPUT_BYTES),
            _read_capped(process.stderr, 200_000),
            process.wait(),
        ),
        timeout=seconds,
    )
    return out, err


async def _stop(process: asyncio.subprocess.Process, container: str) -> None:
    """Kill the container (the real work), then the local docker client, and reap it."""
    await kill(container)
    if process.returncode is None:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
    await process.wait()


async def kill(container: str) -> None:
    if not container:
        return
    process = await asyncio.create_subprocess_exec(
        DOCKER,
        "kill",
        container,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.wait()


def tool_runs(plan: ScanPlan) -> Sequence[ToolRun]:
    builders = {"nuclei": nuclei_run, "zap": zap_run}
    return [builders[tool](plan) for tool in plan.tools]
