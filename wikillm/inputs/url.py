"""Generic URL input adapter.

Phase A: httpx + a tiny stdlib HTML-to-text extractor. Zero extra deps.
Phase B will add a higher-fidelity fetcher (Fetch MCP server or crawl4ai).
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional

import httpx

from ..core.config import Config
from ..core.registry import register_input
from ..core.types import RawItem


_SKIP_TAGS = {"script", "style", "noscript", "head", "iframe", "svg"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._chunks: list[str] = []
        self._title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False
        if tag in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self._title_parts.append(data)
        self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n[ \t]+", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()

    def title(self) -> Optional[str]:
        if not self._title_parts:
            return None
        return " ".join("".join(self._title_parts).split()).strip() or None


class URLInput:
    name = "url"

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        return ref.startswith(("http://", "https://"))

    def fetch(self, config: Config, item: RawItem) -> str:
        url = item.source_ref
        headers = {"User-Agent": config.fetch_user_agent, "Accept": "text/html,text/plain,*/*"}
        with httpx.Client(follow_redirects=True, timeout=config.fetch_timeout_s) as client:
            resp = client.get(url, headers=headers)
        if resp.status_code >= 400:
            raise RuntimeError(f"GET {url} returned {resp.status_code}")
        content_type = resp.headers.get("content-type", "").lower()
        body = resp.content[: config.fetch_max_bytes]
        if "html" in content_type or body[:32].lower().lstrip().startswith(b"<"):
            parser = _TextExtractor()
            try:
                parser.feed(body.decode(resp.encoding or "utf-8", errors="replace"))
            except Exception:
                parser.feed(body.decode("utf-8", errors="replace"))
            return parser.text()
        return body.decode(resp.encoding or "utf-8", errors="replace")


register_input(URLInput())
