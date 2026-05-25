"""Entity-index knowledge stage — extracts `[[wikilinks]]` from each distilled
note into a SQLite index.

Side effect only: writes to `data/entities.db`. Doesn't modify the note or block
the pipeline. Future Phase D work will use this to canonicalize entity names
(merge `[[OpenAI]]` and `[[OpenAI (company)]]`) and to materialize the graph
that Understand-Anything's /understand-knowledge can render.
"""
from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..core.config import Config
from ..core.registry import register_knowledge_stage
from ..core.types import PipelineState


_LINK_RE = re.compile(r"\[\[([^\]\|]+?)(?:\|[^\]]*)?\]\]")


SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    name        TEXT NOT NULL,
    note_path   TEXT NOT NULL,
    PRIMARY KEY (name, note_path)
);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_note ON entities(note_path);
"""


def _db_path(config: Config) -> Path:
    return config.root / "data" / "entities.db"


@contextmanager
def _connect(config: Config) -> Iterator[sqlite3.Connection]:
    p = _db_path(config)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, isolation_level=None)
    try:
        conn.executescript(SCHEMA)
        yield conn
    finally:
        conn.close()


def extract_entities(markdown: str) -> set[str]:
    """Return the unique `[[entity]]` references in `markdown`."""
    out: set[str] = set()
    for m in _LINK_RE.finditer(markdown):
        name = m.group(1).strip()
        if name:
            out.add(name)
    return out


def index_entities_for_note(config: Config, note_path: str, markdown: str) -> int:
    entities = extract_entities(markdown)
    with _connect(config) as conn:
        conn.execute("DELETE FROM entities WHERE note_path = ?", (note_path,))
        if entities:
            conn.executemany(
                "INSERT OR IGNORE INTO entities (name, note_path) VALUES (?, ?)",
                [(e, note_path) for e in entities],
            )
    return len(entities)


def all_entities(config: Config) -> list[tuple[str, int]]:
    """Return `(name, mention_count)` sorted by count desc, name asc."""
    with _connect(config) as conn:
        rows = conn.execute(
            "SELECT name, COUNT(DISTINCT note_path) AS n "
            "FROM entities GROUP BY name "
            "ORDER BY n DESC, name ASC"
        ).fetchall()
    return [(r[0], int(r[1])) for r in rows]


def notes_for_entity(config: Config, name: str) -> list[str]:
    with _connect(config) as conn:
        rows = conn.execute(
            "SELECT note_path FROM entities WHERE name = ? ORDER BY note_path", (name,)
        ).fetchall()
    return [r[0] for r in rows]


class EntityIndexStage:
    name = "entity-index"

    def run(self, config: Config, state: PipelineState) -> None:
        if state.distilled is None or state.distilled.note_path is None:
            return
        n = index_entities_for_note(
            config, state.distilled.note_path, state.distilled.markdown
        )
        state.artifacts["entities_indexed"] = n


register_knowledge_stage(EntityIndexStage())
