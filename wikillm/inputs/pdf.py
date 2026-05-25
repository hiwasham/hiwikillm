"""PDF input adapter — extracts text via pypdf.

Local files only for now. Supports both `item.source_ref` as a path (typical from
`drive-scan` or manual enqueue) and `kind_hint="pdf"`.
"""
from __future__ import annotations

from pathlib import Path

from ..core.config import Config
from ..core.registry import register_input
from ..core.types import RawItem


class PDFInput:
    name = "pdf"

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        if kind_hint == "pdf":
            return True
        p = Path(ref)
        return p.exists() and p.is_file() and p.suffix.lower() == ".pdf"

    def fetch(self, config: Config, item: RawItem) -> str:
        from pypdf import PdfReader  # lazy
        p = Path(item.source_ref)
        if not p.is_file():
            raise FileNotFoundError(f"pdf not found: {p}")

        reader = PdfReader(str(p))
        info = reader.metadata or {}
        title = info.get("/Title") or p.stem
        author = info.get("/Author") or ""

        parts = [f"Title: {title}"]
        if author:
            parts.append(f"Author: {author}")
        parts.append(f"Pages: {len(reader.pages)}")
        parts.append("")

        for i, page in enumerate(reader.pages, 1):
            try:
                text = (page.extract_text() or "").strip()
            except Exception as e:
                text = f"[page {i} extraction error: {e!r}]"
            if text:
                parts.append(f"--- Page {i} ---")
                parts.append(text)
        return "\n".join(parts)


register_input(PDFInput())
