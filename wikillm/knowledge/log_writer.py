"""Log-writer knowledge stage — append-only human-readable record of pipeline runs.

Writes one entry per processed note to `notes/log.md` so you can scan the vault in
Obsidian and see what wikillm has been doing without opening any DB.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from ..core.config import Config
from ..core.registry import register_knowledge_stage
from ..core.types import PipelineState


class LogWriterStage:
    name = "log-writer"

    def run(self, config: Config, state: PipelineState) -> None:
        if state.distilled is None:
            return
        log_path = config.notes_dir / "log.md"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        np = state.distilled.note_path or ""
        try:
            rel = Path(np).relative_to(config.notes_dir) if np else "(unknown)"
        except ValueError:
            rel = np
        chunks = state.artifacts.get("milvus_chunks", 0)
        entities = state.artifacts.get("entities_indexed", 0)

        block = (
            f"## {now} — captured ({state.item.kind})\n"
            f"- title: [[{state.distilled.title}]]\n"
            f"- source: {state.item.source_ref}\n"
            f"- chunks indexed: {chunks}\n"
            f"- entities: {entities}\n"
            f"- path: `{rel}`\n\n"
        )

        # Header on first write.
        if not log_path.exists():
            log_path.write_text(
                "# wikillm — operations log\n\n"
                "_Append-only record of every distillation. Most recent at the top of each session._\n\n",
                encoding="utf-8",
            )

        with log_path.open("a", encoding="utf-8") as f:
            f.write(block)


register_knowledge_stage(LogWriterStage())
