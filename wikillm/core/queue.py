"""SQLite inbox queue. Single table; FIFO with a status field."""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS inbox (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT NOT NULL,
    source_ref    TEXT NOT NULL,
    raw_payload   TEXT,
    status        TEXT NOT NULL DEFAULT 'pending',
    error         TEXT,
    note_path     TEXT,
    captured_at   REAL NOT NULL,
    started_at    REAL,
    finished_at   REAL
);
CREATE INDEX IF NOT EXISTS idx_inbox_status ON inbox(status, captured_at);
"""


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
    finally:
        conn.close()


def enqueue(db_path: Path, kind: str, source_ref: str, raw_payload: Optional[str] = None) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO inbox (kind, source_ref, raw_payload, captured_at) VALUES (?,?,?,?)",
            (kind, source_ref, raw_payload, time.time()),
        )
        return int(cur.lastrowid)


def claim_one(db_path: Path) -> Optional[sqlite3.Row]:
    with connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM inbox WHERE status = 'pending' ORDER BY captured_at LIMIT 1"
        ).fetchone()
        if row is None:
            conn.execute("COMMIT")
            return None
        conn.execute(
            "UPDATE inbox SET status='processing', started_at=? WHERE id=?",
            (time.time(), row["id"]),
        )
        conn.execute("COMMIT")
        return row


def mark_done(db_path: Path, row_id: int, note_path: str) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE inbox SET status='done', note_path=?, finished_at=? WHERE id=?",
            (note_path, time.time(), row_id),
        )


def mark_error(db_path: Path, row_id: int, error: str) -> None:
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE inbox SET status='error', error=?, finished_at=? WHERE id=?",
            (error, time.time(), row_id),
        )


def stats(db_path: Path) -> dict[str, int]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM inbox GROUP BY status"
        ).fetchall()
    return {r["status"]: int(r["n"]) for r in rows}
