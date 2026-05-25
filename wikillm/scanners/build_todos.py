"""build_todos — extract `## Open questions` from each note into `todos/index.md`.

Surfaces the LLM-curator's "what to dig into next" prompts as an actionable
research-priority list. Cron-friendly: idempotent, overwrites `todos/index.md`.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..core.config import Config
from ..core.vaults import vault_notes_dir, vault_todos_dir


_OPEN_Q_RE = re.compile(
    r"^##\s+Open\s+questions\s*$(.*?)(?=^##\s|\Z)",
    flags=re.MULTILINE | re.DOTALL | re.IGNORECASE,
)
_BULLET_RE = re.compile(r"^\s*-\s+(.+?)\s*$", flags=re.MULTILINE)
_TITLE_RE = re.compile(r'^title:\s*"?(.+?)"?\s*$', flags=re.MULTILINE)
_SOURCE_RE = re.compile(r'^source:\s*"?(.+?)"?\s*$', flags=re.MULTILINE)


def extract_open_questions(md: str) -> list[str]:
    """Return bullet items from the `## Open questions` section of a note."""
    m = _OPEN_Q_RE.search(md)
    if not m:
        return []
    return [b.strip() for b in _BULLET_RE.findall(m.group(1))]


def build_todos(config: Config, *, vault: str = "default") -> Path:
    notes_dir = vault_notes_dir(config, vault)
    todos_dir = vault_todos_dir(config, vault)
    todos_dir.mkdir(parents=True, exist_ok=True)
    out = todos_dir / "index.md"

    note_count = 0
    q_count = 0
    sections: list[str] = []

    from ..core.vaults import list_vaults
    other_vault_dirs = set()
    if vault == "default":
        for v in list_vaults(config):
            if v != "default":
                other_vault_dirs.add(notes_dir / v)
    for p in sorted(notes_dir.rglob("*.md")):
        if any(d in p.parents for d in other_vault_dirs):
            continue
        if p.name in {"index.md", "log.md"}:
            continue
        md = p.read_text(encoding="utf-8", errors="replace")
        questions = extract_open_questions(md)
        if not questions:
            continue
        title_m = _TITLE_RE.search(md)
        title = title_m.group(1).strip() if title_m else p.stem
        source_m = _SOURCE_RE.search(md)
        source = source_m.group(1).strip() if source_m else ""
        rel = p.relative_to(notes_dir)

        section_lines = [f"## From [[{title}]]"]
        section_lines.append(f"_`{rel}`{('  •  ' + source) if source else ''}_")
        section_lines.append("")
        for q in questions:
            section_lines.append(f"- [ ] {q}")
        section_lines.append("")
        sections.append("\n".join(section_lines))
        note_count += 1
        q_count += len(questions)

    vault_label = "" if vault == "default" else f" — vault `{vault}`"
    header = [
        f"# wikillm — open questions{vault_label}",
        "",
        "_Surfaced by the LLM curator from each distilled note's `## Open questions` "
        "section. Useful as a research-priority queue: pick one, capture sources that "
        "answer it (`/capture` in Telegram or drop into Drive sources/), let wikillm "
        "distill, and the answer joins your vault._",
        "",
        f"_{q_count} open questions across {note_count} notes._",
        "",
    ]
    out.write_text("\n".join(header) + "\n".join(sections), encoding="utf-8")
    return out
