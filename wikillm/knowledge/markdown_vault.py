"""Markdown-vault stage — writes the DistilledNote to disk under notes/YYYY/MM/.

For non-default vaults the path nests under `notes/<vault>/YYYY/MM/`. The default
vault preserves the pre-multivault layout (notes directly in `notes/YYYY/MM/`).
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..core.config import Config
from ..core.registry import register_knowledge_stage
from ..core.types import DistilledNote, PipelineState
from ..core.vaults import vault_notes_dir


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
        path = _write(vault_notes_dir(config, state.item.vault), state.distilled)
        state.distilled = replace(state.distilled, note_path=str(path))
        state.artifacts["note_path"] = str(path)


register_knowledge_stage(MarkdownVaultStage())
