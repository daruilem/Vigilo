"""Consent log: who started which active scan, on which domain, with which proof.

This is the only thing Vigilo keeps about active scans. It exists so that every scan
can be traced back to a verified request if its owner, or anyone else, asks.

With VIGILO_CONSENT_LOG set, each entry is appended to that file as one JSON line;
otherwise it goes to the application log. The client IP address is personal data:
keep the file only as long as you need it to answer questions (for example 90 days)
and say so in your privacy notice.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("vigilo.consent")


def record(event: str, **fields: Any) -> dict[str, Any]:
    entry = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event}
    entry.update(fields)
    line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    path = os.environ.get("VIGILO_CONSENT_LOG", "")
    if path:
        with Path(path).open("a", encoding="utf-8", newline="\n") as log:
            log.write(line + "\n")
    else:
        logger.info(line)
    return entry
