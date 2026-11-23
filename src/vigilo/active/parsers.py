"""Read the output of the active scanning tools into one common shape.

Supported formats:
- Nuclei: JSON lines (`nuclei -jsonl`), one object per match.
- OWASP ZAP: the JSON report (`zap-baseline.py -J report.json`).

Two rules apply to everything read here:

1. Scope. Only results on the verified host are kept. A tool that followed a redirect to
   another site must not report on it: its owner never agreed to be tested.
2. No site data. Tools copy parts of responses into their output (extracted values,
   evidence snippets, full requests and responses), which may contain passwords or
   customer data. None of it is kept: only the address, the parameter name and the
   tool's own description of the problem.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

from vigilo.models import Severity

MAX_URL_LENGTH = 200

NUCLEI_SEVERITY = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "info": Severity.INFO,
    "unknown": Severity.LOW,
}
ZAP_RISK = {"3": Severity.HIGH, "2": Severity.MEDIUM, "1": Severity.LOW, "0": Severity.INFO}
ZAP_FALSE_POSITIVE, ZAP_LOW_CONFIDENCE = "0", "1"

_CWE = re.compile(r"(?:cwe-)?(\d+)", re.IGNORECASE)
_CVE = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)


@dataclass(frozen=True)
class Location:
    url: str
    parameter: str = ""


@dataclass
class ToolResult:
    tool: str  # "nuclei" or "zap"
    rule: str  # template id or ZAP plugin id
    name: str  # the tool's own English name for the problem, shown as-is
    severity: Severity
    locations: list[Location] = field(default_factory=list)
    tags: frozenset[str] = frozenset()
    cwe: frozenset[int] = frozenset()
    cve: frozenset[str] = frozenset()
    references: list[str] = field(default_factory=list)
    uncertain: bool = False  # the tool itself is not confident


def _host(url: str) -> str:
    try:
        return (urlsplit(url).hostname or "").rstrip(".").lower()
    except ValueError:
        return ""


def in_scope(url: str, domain: str) -> bool:
    return _host(url) == domain


def _clean_url(url: str) -> str:
    """Drop the fragment and cut very long addresses (attack payloads can be huge)."""
    url = url.split("#", 1)[0]
    return url if len(url) <= MAX_URL_LENGTH else url[: MAX_URL_LENGTH - 1] + "…"


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    if isinstance(value, list):
        return [str(v).strip() for v in value if v is not None and str(v).strip()]
    return []


def _cwe_ids(values: list[str]) -> frozenset[int]:
    ids = set()
    for value in values:
        match = _CWE.fullmatch(value.strip())
        if match and match.group(1) != "0":
            ids.add(int(match.group(1)))
    return frozenset(ids)


def _web_links(values: list[str], limit: int = 3) -> list[str]:
    return [v for v in values if v.startswith(("https://", "http://"))][:limit]


# --- Nuclei ----------------------------------------------------------------------------


def parse_nuclei(output: str, domain: str) -> list[ToolResult]:
    """One ToolResult per template, with every matched address in scope."""
    by_template: dict[str, ToolResult] = {}
    for line in output.splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue  # progress messages or a truncated last line
        if not isinstance(item, dict) or item.get("matcher-status") is False:
            continue
        template = str(item.get("template-id") or "")
        url = str(item.get("matched-at") or item.get("url") or item.get("host") or "")
        if not template or not in_scope(url, domain):
            continue
        info = item.get("info")
        info = info if isinstance(info, dict) else {}
        classification = info.get("classification")
        classification = classification if isinstance(classification, dict) else {}
        location = Location(url=_clean_url(url))

        result = by_template.get(template)
        if result is None:
            result = ToolResult(
                tool="nuclei",
                rule=template,
                name=str(info.get("name") or template)[:120],
                severity=NUCLEI_SEVERITY.get(str(info.get("severity")).lower(), Severity.LOW),
                tags=frozenset(t.lower() for t in _as_list(info.get("tags"))),
                cwe=_cwe_ids(_as_list(classification.get("cwe-id"))),
                cve=frozenset(
                    c.upper() for c in _as_list(classification.get("cve-id")) if _CVE.fullmatch(c)
                ),
                references=_web_links(_as_list(info.get("reference"))),
            )
            by_template[template] = result
        if location not in result.locations:
            result.locations.append(location)
    return list(by_template.values())


# --- OWASP ZAP -------------------------------------------------------------------------

_HTML_TAG = re.compile(r"<[^>]+>")


def parse_zap(report: str, domain: str) -> list[ToolResult]:
    try:
        data = json.loads(report)
    except ValueError:
        return []
    results: dict[str, ToolResult] = {}
    sites = data.get("site") if isinstance(data, dict) else None
    for site in sites if isinstance(sites, list) else []:
        if not isinstance(site, dict):
            continue
        for alert in site.get("alerts") or []:
            if not isinstance(alert, dict):
                continue
            confidence = str(alert.get("confidence", ""))
            if confidence == ZAP_FALSE_POSITIVE:
                continue
            locations = [
                Location(url=_clean_url(str(i.get("uri", ""))), parameter=str(i.get("param", "")))
                for i in alert.get("instances") or []
                if isinstance(i, dict) and in_scope(str(i.get("uri", "")), domain)
            ]
            if not locations:
                continue
            rule = str(alert.get("pluginid") or alert.get("alertRef") or "")
            result = results.get(rule)
            if result is None:
                references = _HTML_TAG.sub("\n", str(alert.get("reference", ""))).split()
                result = ToolResult(
                    tool="zap",
                    rule=rule,
                    name=str(alert.get("alert") or alert.get("name") or rule)[:120],
                    severity=ZAP_RISK.get(str(alert.get("riskcode")), Severity.LOW),
                    cwe=_cwe_ids(_as_list(str(alert.get("cweid", "")))),
                    references=_web_links(references),
                    uncertain=confidence == ZAP_LOW_CONFIDENCE,
                )
                results[rule] = result
            for location in locations:
                if location not in result.locations:
                    result.locations.append(location)
    return list(results.values())
