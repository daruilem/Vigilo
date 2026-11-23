"""Translation of reader-facing text.

English is the source language: checks and guidance write English sentences, and each
catalog in `vigilo.locales` maps those exact sentences to a translation. Sentences with
variable parts are written as templates, for example

    "The certificate expires in {days} days."  ->  "Le certificat expire dans {days} jours."

A template is turned into a regular expression; the variable parts are captured from the
English text and placed into the translation. Code snippets are never translated.

Missing translations fall back to English. `tests/test_i18n.py` makes sure none are
missing for the sentences the checks can produce.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from functools import cache
from typing import Any

from vigilo.locales import ar, de, fr
from vigilo.models import Finding, Fix, Observation, ScanReport

LANGUAGES = ("en", "fr", "de", "ar")
DEFAULT_LANGUAGE = "en"

CATALOGS: dict[str, Mapping[str, str]] = {"fr": fr.MESSAGES, "de": de.MESSAGES, "ar": ar.MESSAGES}
CONJUNCTION = {"fr": " et ", "de": " und ", "ar": " و"}

_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def _pattern(template: str) -> re.Pattern[str]:
    parts: list[str] = []
    position = 0
    for match in _PLACEHOLDER.finditer(template):
        parts.append(re.escape(template[position : match.start()]))
        parts.append(f"(?P<{match.group(1)}>.+?)")
        position = match.end()
    parts.append(re.escape(template[position:]))
    return re.compile("^" + "".join(parts) + "$", re.DOTALL)


@cache
def _compiled(language: str) -> tuple[dict[str, str], list[tuple[re.Pattern[str], str]]]:
    catalog = CATALOGS[language]
    exact = {k: v for k, v in catalog.items() if not _PLACEHOLDER.search(k)}
    templates = [(k, v) for k, v in catalog.items() if _PLACEHOLDER.search(k)]
    # Most specific first: the template with the most fixed text wins.
    templates.sort(key=lambda kv: len(_PLACEHOLDER.sub("", kv[0])), reverse=True)
    return exact, [(_pattern(k), v) for k, v in templates]


def _fill(template: str, values: Mapping[str, str]) -> str:
    return _PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), template)


def translate(text: str | None, language: str) -> str | None:
    if not text or language not in CATALOGS:
        return text
    exact, templates = _compiled(language)
    if text in exact:
        return exact[text]
    for pattern, target in templates:
        match = pattern.match(text)
        if match:
            values = {k: _translate_value(v, language) for k, v in match.groupdict().items()}
            return _fill(target, values)
    return text


def _translate_value(value: str, language: str) -> str:
    exact, _ = _compiled(language)
    if value in exact:
        return exact[value]
    return value.replace(" and ", CONJUNCTION[language])


def is_supported(language: str) -> bool:
    return language in LANGUAGES


def localize_finding(finding: Finding, language: str) -> Finding:
    if language not in CATALOGS:
        return finding

    def tr(text: str | None) -> str | None:
        return translate(text, language)

    return finding.model_copy(
        update={
            "title": tr(finding.title),
            "headline": tr(finding.headline),
            "description": tr(finding.description),
            "recommendation": tr(finding.recommendation),
            "note": tr(finding.note),
            "follow_up": tr(finding.follow_up),
            "observed": [
                Observation(label=tr(o.label) or o.label, value=tr(o.value) or o.value)
                for o in finding.observed
            ],
            "fixes": {
                platform: Fix(intro=tr(fix.intro) or fix.intro, code=fix.code)
                for platform, fix in finding.fixes.items()
            },
        }
    )


def localize_report(report: ScanReport, language: str) -> ScanReport:
    if language not in CATALOGS:
        return report
    return report.model_copy(
        update={"findings": [localize_finding(f, language) for f in report.findings]}
    )


def localize_event(event: dict[str, Any], language: str) -> dict[str, Any]:
    if language not in CATALOGS or event.get("type") != "plan":
        return event
    steps = [{**step, "label": translate(step["label"], language)} for step in event["steps"]]
    return {**event, "steps": steps}
