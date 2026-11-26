"""Data models shared by every check, the scorer, the CLI and the API.

Every check returns a list of `Finding` objects. Scoring, reporting and the API only
depend on this format, so adding a new check never requires touching them.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Status(str, Enum):
    PASS = "pass"  # noqa: S105 - not a password
    WARN = "warn"
    FAIL = "fail"
    INFO = "info"
    ERROR = "error"  # the check itself could not run


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Platform(str, Enum):
    APACHE = "apache"
    NGINX = "nginx"
    CLOUDFLARE = "cloudflare"
    WORDPRESS = "wordpress"


class Observation(BaseModel):
    """A raw value seen during the scan, shown as-is in the report."""

    label: str
    value: str


class Fix(BaseModel):
    intro: str = Field(description="One or two sentences: where to put the code.")
    code: str


class Finding(BaseModel):
    id: str = Field(description="Stable identifier, e.g. 'headers.hsts'.")
    check: str = Field(description="Name of the check that produced this finding.")
    title: str = Field(description="Technical name of what was checked.")
    headline: str | None = Field(
        default=None, description="Plain-language sentence describing the result."
    )
    status: Status
    severity: Severity = Severity.INFO
    description: str = Field(description="Plain-language explanation for non-experts.")
    recommendation: str | None = None
    observed: list[Observation] = Field(default_factory=list)
    note: str | None = None
    fixes: dict[Platform, Fix] = Field(default_factory=dict)
    follow_up: str | None = None
    references: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ScanReport(BaseModel):
    target: str
    kind: Literal["passive", "active"] = Field(
        default="passive",
        description="Passive check-up, or active scan of a verified domain (graded separately).",
    )
    started_at: datetime
    finished_at: datetime
    score: int = Field(ge=0, le=100)
    grade: str
    findings: list[Finding]
    signature: str | None = Field(
        default=None,
        description="HMAC issued by this server, required to turn the report into a PDF.",
    )
