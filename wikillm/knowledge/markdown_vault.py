"""Markdown-vault stage — writes the DistilledNote to disk under notes/YYYY/MM/.

Phase B: this directory will live inside Drive so it syncs into the Obsidian vault.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..core.config import Config
from ..core.registry import register_knowledge_stage
from ..core.types import DistilledNote, PipelineState


def _write(notes_dir: Path, note: DistilledNote) -> Path:
    sub = notes_dir / f"{note.captured_at:%Y/%m}"
    sub.mkdir(parents=True, exist_ok=True)
    out = sub / f"{note.slug}.md"
    counter = 2
    while out.exists():
        out = sub / f"{note.slug}-{counter}.md"
        counter += 1
    out.write_text(note.markdown, encoding="utf-8")
    return out


class MarkdownVaultStage:
    name = "markdown-vault"

    def run(self, config: Config, state: PipelineState) -> None:
        if state.distilled is None:
            raise RuntimeError("markdown-vault: no distilled note in state (run llm-distill first)")
        path = _write(config.notes_dir, state.distilled)
        state.distilled = replace(state.distilled, note_path=str(path))
        state.artifacts["note_path"] = str(path)


register_knowledge_stage(MarkdownVaultStage())
