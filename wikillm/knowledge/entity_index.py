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


TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS entities (
    name        TEXT NOT NULL,
    note_path   TEXT NOT NULL,
    vault       TEXT NOT NULL DEFAULT 'default',
    PRIMARY KEY (name, note_path)
);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_note ON entities(note_path);
"""

# Kept for backward compat — older callers imported SCHEMA.
SCHEMA = TABLE_SCHEMA


def _ensure_vault_column(conn) -> None:
    """Add the vault column to pre-existing DBs + create its index. Idempotent."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(entities)").fetchall()}
    if "vault" not in cols:
        conn.execute("ALTER TABLE entities ADD COLUMN vault TEXT NOT NULL DEFAULT 'default'")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_vault ON entities(vault)")


def _db_path(config: Config) -> Path:
    return config.root / "data" / "entities.db"


@contextmanager
def _connect(config: Config) -> Iterator[sqlite3.Connection]:
    p = _db_path(config)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, isolation_level=None)
    try:
        conn.executescript(TABLE_SCHEMA)
        _ensure_vault_column(conn)   # migrates old DBs + creates vault index
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


def index_entities_for_note(config: Config, note_path: str, markdown: str, vault: str = "default") -> int:
    entities = extract_entities(markdown)
    with _connect(config) as conn:
        conn.execute("DELETE FROM entities WHERE note_path = ?", (note_path,))
        if entities:
            conn.executemany(
                "INSERT OR IGNORE INTO entities (name, note_path, vault) VALUES (?, ?, ?)",
                [(e, note_path, vault) for e in entities],
            )
    return len(entities)


def all_entities(config: Config, vault: str | None = None) -> list[tuple[str, int]]:
    """Return `(name, mention_count)`. If `vault` is None, sum across all vaults."""
    with _connect(config) as conn:
        if vault is None:
            rows = conn.execute(
                "SELECT name, COUNT(DISTINCT note_path) AS n "
                "FROM entities GROUP BY name "
                "ORDER BY n DESC, name ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT name, COUNT(DISTINCT note_path) AS n "
                "FROM entities WHERE vault = ? GROUP BY name "
                "ORDER BY n DESC, name ASC",
                (vault,),
            ).fetchall()
    return [(r[0], int(r[1])) for r in rows]


def notes_for_entity(config: Config, name: str, vault: str | None = None) -> list[str]:
    with _connect(config) as conn:
        if vault is None:
            rows = conn.execute(
                "SELECT note_path FROM entities WHERE name = ? ORDER BY note_path", (name,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT note_path FROM entities WHERE name = ? AND vault = ? ORDER BY note_path",
                (name, vault),
            ).fetchall()
    return [r[0] for r in rows]


class EntityIndexStage:
    name = "entity-index"

    def run(self, config: Config, state: PipelineState) -> None:
        if state.distilled is None or state.distilled.note_path is None:
            return
        n = index_entities_for_note(
            config,
            state.distilled.note_path,
            state.distilled.markdown,
            vault=state.item.vault,
        )
        state.artifacts["entities_indexed"] = n


register_knowledge_stage(EntityIndexStage())
