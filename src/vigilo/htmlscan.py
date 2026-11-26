"""Minimal HTML reader for content checks: links, resources, language, generator.

Uses the standard library parser, which never executes anything. Only the HTML that
the server returned is seen: content added later by JavaScript is invisible here.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class Link:
    href: str
    text: str


@dataclass
class PageInfo:
    lang: str = ""
    links: list[Link] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)  # script, link, iframe, img sources
    generator: str = ""
    # Codes of <meta name="vigilo-verification"> tags found in the <head> only: visitors can
    # add content to the body of some pages (comments, reviews), never to the head.
    verification_codes: list[str] = field(default_factory=list)


class _Reader(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.info = PageInfo()
        self._href: str | None = None
        self._text: list[str] = []
        self._in_body = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "body":
            self._in_body = True
        if tag == "html" and not self.info.lang:
            self.info.lang = a.get("lang", "").lower()
        elif tag == "a":
            self._href = a.get("href", "")
            self._text = [a.get("aria-label", ""), a.get("title", "")]
        elif tag in ("script", "iframe", "img") and a.get("src"):
            self.info.resources.append(a["src"])
        elif tag == "link" and a.get("href"):
            self.info.resources.append(a["href"])
        elif tag == "meta" and a.get("name", "").lower() == "generator":
            self.info.generator = self.info.generator or a.get("content", "")
        elif (
            tag == "meta"
            and not self._in_body
            and a.get("name", "").lower() == "vigilo-verification"
        ):
            self.info.verification_codes.append(a.get("content", "").strip())

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            text = " ".join(" ".join(self._text).split())
            self.info.links.append(Link(href=self._href, text=text))
            self._href = None


def read_page(html: str) -> PageInfo:
    reader = _Reader()
    with contextlib.suppress(Exception):  # malformed HTML: keep whatever was read
        reader.feed(html)
        reader.close()
    return reader.info
