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
from ..core.vaults import DEFAULT_VAULT, list_vaults, vault_sources_dir


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


def _scan_one_vault(config: Config, vault: str) -> int:
    """Scan a single vault's sources subdirectory. Returns enqueued count."""
    src_dir = vault_sources_dir(config, vault)
    if not src_dir.exists():
        return 0
    enqueued = 0
    for p in sorted(src_dir.rglob("*")):
        if not p.is_file():
            continue
        # Skip anything inside a sibling vault subdir (avoid double-counting from default scan)
        if vault == DEFAULT_VAULT:
            try:
                rel_parent = p.parent.relative_to(src_dir).parts
                if rel_parent and not rel_parent[0].isdigit() and rel_parent[0] in {
                    v for v in list_vaults(config) if v != DEFAULT_VAULT
                }:
                    continue
            except ValueError:
                pass
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
            source_ref = url
        elif kind == "text":
            source_ref = str(p)
            payload = _payload_for_text(p)
            if not payload.strip():
                continue
        else:
            source_ref = str(p)
        if _already_seen(config.inbox_db, source_ref):
            continue
        # Encode vault in extras so the pipeline routes correctly.
        # (queue stores it as JSON in raw_payload when payload is None — simpler:
        # use a dedicated column? For now: prefix raw_payload with a vault marker
        # when kind != "text" by encoding into a JSON header. Cleanest: add a
        # vault column to the inbox schema.)
        queue.enqueue_with_vault(config.inbox_db, kind, source_ref, payload, vault)
        enqueued += 1
    return enqueued


def scan_sources_dir(config: Config, vault: str | None = None) -> int:
    """Scan a single vault, or every vault when `vault` is None."""
    if vault is not None:
        return _scan_one_vault(config, vault)
    total = 0
    for v in list_vaults(config):
        total += _scan_one_vault(config, v)
    return total
