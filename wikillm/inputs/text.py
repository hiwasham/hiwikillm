"""Text input adapter — for inline text payloads (clipboard snippets, free-text drops).

The text is carried inside RawItem.raw_payload. This adapter exists so the pipeline
treats text the same way as any other input — no special case in pipeline.py.
"""
from __future__ import annotations

from ..core.config import Config
from ..core.registry import register_input
from ..core.types import RawItem


class TextInput:
    name = "text"

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        # Only match when the kind is explicitly "text" — otherwise we'd swallow
        # everything (since any string "matches" as text).
        return kind_hint == "text"

    def fetch(self, config: Config, item: RawItem) -> str:
        if item.raw_payload is not None:
            return item.raw_payload
        return item.source_ref


register_input(TextInput())
