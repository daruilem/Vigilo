"""HTTP API. Run with: uvicorn vigilo.api:app --no-server-header --no-proxy-headers

Two ways to scan:
- POST /api/v1/scans returns the report when the scan is finished.
- GET /api/v1/scans/stream sends Server-Sent Events: progress steps, then the report
  (or a failure). This is what the web interface uses to show the live log.

Nothing is stored: reports only exist in the response.

Abuse protection, applied before any network activity:
- explicit authorisation from the user,
- a limit per client IP (behind trusted proxies only, X-Forwarded-For is believed),
- a limit per target site, so Vigilo cannot be used to hammer one website,
- a cap on concurrent scans and a time limit per scan.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from vigilo import __version__, errors
from vigilo.clientip import client_ip, parse_networks
from vigilo.errors import ScanError
from vigilo.i18n import localize_event, localize_report, translate
from vigilo.models import Platform, ScanReport
from vigilo.pdf import file_name, render_report
from vigilo.ratelimit import RateLimiter
from vigilo.scanner import Event, scan
from vigilo.signing import sign, verify
from vigilo.target import parse_target

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, str(default)))


MAX_TARGET_LENGTH = 300
SCANS_PER_WINDOW = _env_int("VIGILO_SCANS_PER_WINDOW", 10)
SCANS_PER_TARGET = _env_int("VIGILO_SCANS_PER_TARGET", 3)
WINDOW_SECONDS = _env_int("VIGILO_WINDOW_SECONDS", 600)
MAX_CONCURRENT_SCANS = _env_int("VIGILO_MAX_CONCURRENT_SCANS", 8)
SCAN_TIME_LIMIT = _env_int("VIGILO_SCAN_TIME_LIMIT", 60)
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("VIGILO_CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
TRUSTED_PROXIES = parse_networks(os.environ.get("VIGILO_TRUSTED_PROXIES", ""))
DOCS_ENABLED = os.environ.get("VIGILO_DOCS", "0") == "1"

MAX_BODY_BYTES = 1_000_000
PDFS_PER_WINDOW = _env_int("VIGILO_PDFS_PER_WINDOW", 30)

limiter = RateLimiter(SCANS_PER_WINDOW, WINDOW_SECONDS)
pdf_limiter = RateLimiter(PDFS_PER_WINDOW, WINDOW_SECONDS)
target_limiter = RateLimiter(SCANS_PER_TARGET, WINDOW_SECONDS)


class ScanSlots:
    """Counts running scans so the service refuses work instead of slowing down for all."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.active = 0

    def try_acquire(self) -> bool:
        if self.active >= self.capacity:
            return False
        self.active += 1
        return True

    def release(self) -> None:
        self.active = max(0, self.active - 1)


slots = ScanSlots(MAX_CONCURRENT_SCANS)


app = FastAPI(
    title="Vigilo",
    version=__version__,
    description="Free, readable security check-up for small websites.",
    docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url=None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Disposition"],
)

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Resource-Policy": "same-site",
    "Cache-Control": "no-store",
}
DOCS_CSP = (
    "default-src 'none'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net; img-src 'self' https://fastapi.tiangolo.com "
    "data:; connect-src 'self'; frame-ancestors 'none'"
)


@app.middleware("http")
async def limit_body_size(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    length = request.headers.get("content-length")
    if request.method == "POST" and (
        length is None or not length.isdigit() or int(length) > MAX_BODY_BYTES
    ):
        return JSONResponse(
            status_code=413, content={"detail": _error("too_large", errors.TOO_LARGE)}
        )
    return await call_next(request)


@app.middleware("http")
async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    if DOCS_ENABLED and request.url.path == "/docs":
        response.headers["Content-Security-Policy"] = DOCS_CSP
    return response


Language = Literal["en", "fr", "de", "ar"]


class ScanRequest(BaseModel):
    target: str = Field(min_length=1, max_length=MAX_TARGET_LENGTH, examples=["example.com"])
    authorized: bool = Field(
        description="The user confirms they run the website or have permission to check it."
    )
    lang: Language = "en"


def _error(code: str, message: str, lang: str = "en") -> dict[str, str]:
    return {"code": code, "message": translate(message, lang) or message}


def _ip_of(request: Request) -> str:
    peer = request.client.host if request.client else "unknown"
    return client_ip(peer, request.headers.get("x-forwarded-for"), TRUSTED_PROXIES)


def _gate(request: Request, target: str, authorized: bool, lang: str) -> dict[str, str] | None:
    """Checks that apply before any network activity. Returns an error, or None.

    On success a scan slot is held: the caller must release it.
    """
    if not authorized:
        return _error("not_authorized", errors.NOT_AUTHORIZED, lang)
    try:
        host = parse_target(target).hostname
    except ScanError as exc:
        return _error(exc.code, exc.message, lang)
    if not limiter.allow(_ip_of(request)):
        return _error("rate_limited", errors.RATE_LIMITED, lang)
    if not target_limiter.allow(host):
        return _error("target_rate_limited", errors.TARGET_RATE_LIMITED, lang)
    if not slots.try_acquire():
        return _error("busy", errors.BUSY, lang)
    return None


GATE_STATUS = {
    "not_authorized": 403,
    "rate_limited": 429,
    "target_rate_limited": 429,
    "busy": 503,
}


async def _run_limited(
    target: str, on_event: Callable[[Event], Awaitable[None]] | None = None
) -> ScanReport:
    try:
        return await asyncio.wait_for(scan(target, on_event=on_event), timeout=SCAN_TIME_LIMIT)
    except asyncio.TimeoutError as exc:
        raise ScanError(errors.SCAN_TIMEOUT, "timeout") from exc
    finally:
        slots.release()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/scans")
async def create_scan(body: ScanRequest, request: Request) -> ScanReport:
    gate = _gate(request, body.target, body.authorized, body.lang)
    if gate is not None:
        raise HTTPException(status_code=GATE_STATUS.get(gate["code"], 422), detail=gate)
    try:
        report = await _run_limited(body.target)
    except ScanError as exc:
        raise HTTPException(
            status_code=422, detail=_error(exc.code, exc.message, body.lang)
        ) from exc
    return sign(localize_report(report, body.lang))


def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/api/v1/scans/stream")
async def stream_scan(
    request: Request,
    target: str = Query(min_length=1, max_length=MAX_TARGET_LENGTH),
    authorized: bool = False,
    lang: Language = "en",
) -> StreamingResponse:
    # Failures are sent as events too: EventSource cannot read the body of a failed response.
    gate = _gate(request, target, authorized, lang)

    async def events() -> AsyncIterator[str]:
        if gate is not None:
            yield _sse("failure", gate)
            return

        queue: asyncio.Queue[tuple[str, Any] | None] = asyncio.Queue()
        started = False

        async def on_event(event: Event) -> None:
            await queue.put(("progress", localize_event(event, lang)))

        async def run() -> None:
            nonlocal started
            started = True
            try:
                report = await _run_limited(target, on_event)
                signed = sign(localize_report(report, lang))
                await queue.put(("report", signed.model_dump(mode="json")))
            except ScanError as exc:
                await queue.put(("failure", _error(exc.code, exc.message, lang)))
            except Exception:
                logger.exception("Unexpected error during a scan")
                await queue.put(("failure", _error("internal", errors.INTERNAL, lang)))
            finally:
                await queue.put(None)

        task = asyncio.create_task(run())
        try:
            while (item := await queue.get()) is not None:
                yield _sse(*item)
        finally:
            task.cancel()
            if not started:  # cancelled before running: _run_limited never released the slot
                slots.release()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class PdfRequest(BaseModel):
    report: ScanReport
    lang: Language = "en"
    platform: Platform = Platform.APACHE


@app.post("/api/v1/reports/pdf")
async def report_pdf(body: PdfRequest, request: Request) -> Response:
    """Turn a report produced by this server into a PDF. Edited reports are refused."""
    if not pdf_limiter.allow(_ip_of(request)):
        raise HTTPException(
            status_code=429, detail=_error("rate_limited", errors.RATE_LIMITED, body.lang)
        )
    if not verify(body.report):
        raise HTTPException(
            status_code=400, detail=_error("invalid_report", errors.INVALID_REPORT, body.lang)
        )
    pdf = await asyncio.to_thread(render_report, body.report, body.lang, body.platform)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{file_name(body.report)}"'},
    )
