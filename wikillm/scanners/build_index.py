"""build_index — walks notes/, writes a Karpathy-pattern `index.md` at the vault root.

Required for Understand-Anything's `/understand-knowledge` command, useful for
humans browsing the vault in Obsidian, and the canonical entry point for the
whole knowledge base.

Run via `python -m wikillm build-index`. Cron-friendly: idempotent, overwrites
`notes/index.md` each time.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from ..core.config import Config
from ..core.vaults import vault_notes_dir
from ..knowledge.entity_index import all_entities, extract_entities


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_KV_RE = re.compile(r'^(\w+):\s*"?([^"]*)"?\s*$')
_TAG_RE = re.compile(r'^\s+-\s*(.+?)\s*$')


def _parse_frontmatter(md: str) -> tuple[dict[str, str], list[str]]:
    """Return ((scalar fields), (tags))."""
    m = _FRONTMATTER_RE.match(md)
    if not m:
        return {}, []
    fields: dict[str, str] = {}
    tags: list[str] = []
    in_tags = False
    for line in m.group(1).splitlines():
        if line.strip() == "tags:":
            in_tags = True
            continue
        if in_tags:
            tm = _TAG_RE.match(line)
            if tm:
                tags.append(tm.group(1).strip().strip('"\''))
                continue
            in_tags = False  # exited the tags block
        km = _KV_RE.match(line)
        if km:
            fields[km.group(1)] = km.group(2).strip()
    return fields, tags


def build_index(config: Config, *, top_entities: int = 50, vault: str = "default") -> Path:
    notes_dir = vault_notes_dir(config, vault)
    if not notes_dir.exists():
        raise FileNotFoundError(f"notes_dir does not exist for vault {vault!r}: {notes_dir}")

    rows: list[tuple[str, Path, dict[str, str], list[str]]] = []  # title, path, meta, tags
    by_tag: dict[str, list[tuple[str, Path]]] = defaultdict(list)

    from ..core.vaults import list_vaults
    other_vault_dirs = set()
    if vault == "default":
        for v in list_vaults(config):
            if v != "default":
                other_vault_dirs.add(notes_dir / v)
    for p in sorted(notes_dir.rglob("*.md")):
        if p.name in {"index.md", "log.md"}:
            continue
        # When building the default-vault index, skip any path nested under a named-vault dir.
        if any(d in p.parents for d in other_vault_dirs):
            continue
        md = p.read_text(encoding="utf-8", errors="replace")
        meta, tags = _parse_frontmatter(md)
        title = meta.get("title") or p.stem
        rows.append((title, p, meta, tags))
        for t in tags:
            by_tag[t].append((title, p))

    # Fall back to scanning notes for entity counts if entity-index hasn't been populated yet.
    entity_counts = all_entities(config, vault=vault)
    if not entity_counts:
        counts: dict[str, int] = defaultdict(int)
        for _, p, _, _ in rows:
            md = p.read_text(encoding="utf-8", errors="replace")
            for e in extract_entities(md):
                counts[e] += 1
        entity_counts = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    lines: list[str] = []
    vault_label = "" if vault == "default" else f" — vault `{vault}`"
    lines.append(f"# wikillm — index{vault_label}")
    lines.append("")
    lines.append(f"_{len(rows)} notes, {sum(len(v) for v in by_tag.values())} tag links, "
                 f"{len(entity_counts)} unique entities. Regenerate with `wikillm build-index`._")
    lines.append("")

    if by_tag:
        lines.append("## Notes by tag")
        lines.append("")
        for tag in sorted(by_tag):
            lines.append(f"### {tag}")
            for title, p in sorted(by_tag[tag], key=lambda x: x[0].lower()):
                rel = p.relative_to(notes_dir)
                lines.append(f"- [[{title}]] — `{rel}`")
            lines.append("")

    lines.append("## All notes")
    lines.append("")
    for title, p, meta, _tags in sorted(rows, key=lambda r: r[0].lower()):
        rel = p.relative_to(notes_dir)
        src = meta.get("source", "")
        suffix = f" — _{src}_" if src else ""
        lines.append(f"- [[{title}]] — `{rel}`{suffix}")
    lines.append("")

    if entity_counts:
        lines.append(f"## Top entities (top {top_entities} by note count)")
        lines.append("")
        for name, n in entity_counts[:top_entities]:
            lines.append(f"- [[{name}]] ({n})")
        lines.append("")

    out = notes_dir / "index.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out
