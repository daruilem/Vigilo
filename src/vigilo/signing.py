"""Report signatures.

Reports are not stored on the server, so to produce a PDF the browser sends the report
back. The signature proves the report was produced by this server and not edited: it
prevents anyone from generating an official-looking "Vigilo" PDF with invented results.

The key comes from VIGILO_SIGNING_KEY. Without it a random key is created at start-up,
so reports from before a restart can no longer be turned into PDFs (the user simply
runs the check again).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets

from vigilo.models import ScanReport

_KEY = (os.environ.get("VIGILO_SIGNING_KEY") or secrets.token_hex(32)).encode()


def _canonical(report: ScanReport) -> bytes:
    data = report.model_dump(mode="json", exclude={"signature"})
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def tag(purpose: str, *parts: str, key: bytes = _KEY) -> str:
    """HMAC of `parts` for one `purpose`.

    The purpose is part of the signed data, so a value signed for one use (for example a
    domain verification code) can never be accepted for another (an ownership pass).
    """
    message = "\0".join((purpose, *parts)).encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def sign(report: ScanReport, key: bytes = _KEY) -> ScanReport:
    digest = hmac.new(key, _canonical(report), hashlib.sha256).hexdigest()
    return report.model_copy(update={"signature": digest})


def verify(report: ScanReport, key: bytes = _KEY) -> bool:
    if not report.signature:
        return False
    expected = hmac.new(key, _canonical(report), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, report.signature)
