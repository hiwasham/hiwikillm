"""Directory-watcher scanners — enqueue new files dropped into a watched folder.

Run via `python -m wikillm scan` (cron-friendly). Dedups against the inbox by source_ref:
the same path won't be enqueued twice.

Currently watches `config.sources_dir`. After rclone-mounting Drive, point `sources_dir`
at the mount so anything you drop into Drive's /wikillm/sources/ auto-enters the pipeline.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..core import queue
from ..core.config import Config


SUPPORTED_SUFFIXES = {
    ".pdf": "pdf",
    ".txt": "text",
    ".md": "text",
    ".url": "url",
}


def _already_seen(db_path: Path, source_ref: str) -> bool:
    with queue.connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM inbox WHERE source_ref = ? LIMIT 1",
            (source_ref,),
        ).fetchone()
        return row is not None


def _payload_for_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _extract_url_from_url_file(p: Path) -> str | None:
    """A .url file holds one URL on the first non-empty, non-comment line."""
    try:
        for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if line.lower().startswith("url="):
                line = line[4:].strip()
            if line.startswith(("http://", "https://")):
                return line
    except Exception:
        return None
    return None


def scan_sources_dir(config: Config) -> int:
    """Walk config.sources_dir; enqueue any new supported files. Returns count enqueued."""
    if not config.sources_dir.exists():
        return 0
    enqueued = 0
    for p in sorted(config.sources_dir.rglob("*")):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        kind = SUPPORTED_SUFFIXES.get(suf)
        if kind is None:
            continue
        source_ref: str
        payload: str | None = None
        if kind == "url":
            url = _extract_url_from_url_file(p)
            if not url:
                continue
            source_ref = url                 # dedup on the URL itself, not the file path
        elif kind == "text":
            source_ref = str(p)
            payload = _payload_for_text(p)
            if not payload.strip():
                continue
        else:  # pdf or other file-paths
            source_ref = str(p)
        if _already_seen(config.inbox_db, source_ref):
            continue
        queue.enqueue(config.inbox_db, kind, source_ref, payload)
        enqueued += 1
    return enqueued
