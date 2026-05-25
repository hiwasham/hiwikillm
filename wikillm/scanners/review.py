"""Spaced-repetition resurfacing — pick old notes to re-read.

A simple Anki-like schedule tracking per-note review history in `data/reviews.db`.
After review N, the note is next due in `INTERVALS[N]` days. Notes never reviewed
are due once they're at least 1 day old (so a brand-new capture isn't immediately
surfaced).

Usage:
  wikillm review                  # show up to 3 due notes with TL;DR
  wikillm reviewed <slug>         # record that you re-read a note
  # Telegram: /review and /reviewed <slug>
"""
from __future__ import annotations

import datetime as dt
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ..core.config import Config


# Days from last review until next due. After the last interval, repeat the last value.
INTERVALS = [1, 3, 7, 14, 30, 90, 180, 365]


SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    note_path        TEXT PRIMARY KEY,
    last_reviewed_at REAL,
    review_count     INTEGER NOT NULL DEFAULT 0
);
"""


_TITLE_RE = re.compile(r'^title:\s*"?(.+?)"?\s*$', re.MULTILINE)
_TLDR_RE = re.compile(r"^##\s+TL;DR\s*$(.*?)(?=^##\s|\Z)", re.MULTILINE | re.DOTALL)


def _db_path(config: Config) -> Path:
    return config.root / "data" / "reviews.db"


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


def mark_reviewed(config: Config, note_path: str) -> int:
    """Increment review count + timestamp. Returns new review_count."""
    now = dt.datetime.now(dt.timezone.utc).timestamp()
    with _connect(config) as conn:
        conn.execute(
            "INSERT INTO reviews (note_path, last_reviewed_at, review_count) "
            "VALUES (?, ?, 1) "
            "ON CONFLICT(note_path) DO UPDATE SET "
            "  last_reviewed_at = excluded.last_reviewed_at, "
            "  review_count = review_count + 1",
            (note_path, now),
        )
        row = conn.execute(
            "SELECT review_count FROM reviews WHERE note_path = ?", (note_path,)
        ).fetchone()
    return int(row[0]) if row else 1


def get_due(config: Config, *, limit: int = 3) -> list[dict]:
    """Return up to `limit` due notes, sorted by most-overdue first."""
    notes_dir = config.notes_dir
    if not notes_dir.exists():
        return []
    now = dt.datetime.now(dt.timezone.utc).timestamp()

    with _connect(config) as conn:
        reviews_by_path: dict[str, tuple[float, int]] = {
            r[0]: (r[1], int(r[2]))
            for r in conn.execute(
                "SELECT note_path, last_reviewed_at, review_count FROM reviews"
            ).fetchall()
        }

    candidates: list[dict] = []
    for p in notes_dir.rglob("*.md"):
        if p.name in {"index.md", "log.md"}:
            continue
        path_str = str(p)
        last_at, count = reviews_by_path.get(path_str, (None, 0))

        if last_at is None:
            mtime = p.stat().st_mtime
            age_days = (now - mtime) / 86400
            if age_days >= 1:
                candidates.append({
                    "path": p,
                    "last_at": None,
                    "count": 0,
                    "overdue_days": age_days,
                })
        else:
            interval_idx = min(max(count - 1, 0), len(INTERVALS) - 1)
            interval_days = INTERVALS[interval_idx]
            since_last = (now - last_at) / 86400
            if since_last >= interval_days:
                candidates.append({
                    "path": p,
                    "last_at": last_at,
                    "count": count,
                    "overdue_days": since_last - interval_days,
                })

    candidates.sort(key=lambda c: c["overdue_days"], reverse=True)
    return candidates[:limit]


def get_due_summary(config: Config, *, limit: int = 3) -> list[dict]:
    """Same as get_due, enriched with title and TL;DR snippet."""
    due = get_due(config, limit=limit)
    for d in due:
        try:
            md = d["path"].read_text(encoding="utf-8", errors="replace")
        except Exception:
            md = ""
        t_m = _TITLE_RE.search(md)
        d["title"] = t_m.group(1).strip() if t_m else d["path"].stem
        tldr_m = _TLDR_RE.search(md)
        d["tldr"] = (tldr_m.group(1).strip() if tldr_m else "")[:600]
    return due


def find_note_by_slug(config: Config, slug: str) -> list[Path]:
    """Find note path(s) matching a partial slug/filename."""
    matches = []
    for p in config.notes_dir.rglob("*.md"):
        if p.name in {"index.md", "log.md"}:
            continue
        if slug in p.name or slug in p.stem:
            matches.append(p)
    return matches
