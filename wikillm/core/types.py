"""Shared data types and plugin protocols for the three-layer architecture.

Three layers:
  inputs    - source adapters that fetch raw text from somewhere
  knowledge - stages that transform/store distilled content
  outputs   - consumers of the knowledge layer that emit something for the user

Each layer's plugins are duck-typed against the protocols below. Drop-in: write a
class implementing the protocol, register it in the matching layer registry.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class RawItem:
    """A unit of input flowing into the system. Source-agnostic."""

    kind: str                                # url|youtube|github|pdf|text|file|telegram|...
    source_ref: str                          # URL, file path, or short identifier
    raw_payload: str | None = None           # inline content for text-kind items
    extras: dict[str, Any] = field(default_factory=dict)
    vault: str = "default"                   # multi-vault routing (Phase E)


@dataclass(frozen=True)
class DistilledNote:
    """LLM-distilled structured Markdown note. The unit of knowledge."""

    markdown: str
    title: str
    slug: str
    raw_item: RawItem
    captured_at: dt.datetime
    note_path: str | None = None             # set once written to disk by markdown-vault

    @property
    def vault(self) -> str:
        return self.raw_item.vault


@runtime_checkable
class InputAdapter(Protocol):
    """Plugin that fetches source content for a given reference.

    Examples: url, youtube, github, pdf, telegram-forward, drive-scan, notebooklm, rss, ...
    """

    name: str

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        """Return True if this adapter can handle the given ref."""

    def fetch(self, config, item: "RawItem") -> str:
        """Return the source content as text. May raise on network/parse errors."""


@runtime_checkable
class KnowledgeStage(Protocol):
    """A single step in the knowledge pipeline.

    Stages run in order. Each receives the current pipeline state (item, source text,
    distilled note if produced) and may mutate or replace fields. Examples: llm-distill
    (raw text -> DistilledNote), markdown-vault (DistilledNote -> file on disk),
    milvus-index (DistilledNote -> embedded chunks), entity-link (DistilledNote -> augmented).
    """

    name: str

    def run(self, config, state: "PipelineState") -> None:
        """Mutate `state` in place — set state.distilled, write side effects, etc."""


@runtime_checkable
class OutputAdapter(Protocol):
    """Plugin that consumes the knowledge layer and emits something user-facing.

    Examples: telegram-qa, weekly-digest-email, video-summary, podcast-generator,
    dashboard, graph-viz.
    """

    name: str

    def serve(self, config, registry) -> None:
        """Start or run this output. For long-running outputs (bots, servers), block."""


@dataclass
class PipelineState:
    """Mutable state passed through the knowledge stages for one RawItem."""

    item: RawItem
    source_text: str | None = None
    distilled: DistilledNote | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)
