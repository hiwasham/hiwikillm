"""Multi-vault path + collection helpers.

A "vault" partitions the knowledge base into separate domains (work / personal /
research / books / ...). Each vault has its own:
- notes directory subtree
- Milvus collection (semantic index)
- log.md, index.md, todos
- entity-index rows (scoped via the `vault` column)

The "default" vault preserves the pre-multivault layout for backward compatibility:
notes live directly at `notes_dir/YYYY/MM/<slug>.md` and Milvus collection is
just `wikillm_notes` (whatever's configured). Named vaults nest under their name.
"""
from __future__ import annotations

from pathlib import Path

from .config import Config


DEFAULT_VAULT = "default"


def is_default(vault: str | None) -> bool:
    return not vault or vault == DEFAULT_VAULT


def vault_notes_dir(config: Config, vault: str) -> Path:
    """Where this vault's distilled notes live."""
    if is_default(vault):
        return config.notes_dir
    return config.notes_dir / vault


def vault_sources_dir(config: Config, vault: str) -> Path:
    if is_default(vault):
        return config.sources_dir
    return config.sources_dir / vault


def vault_todos_dir(config: Config, vault: str) -> Path:
    base = config.root / "todos"
    if is_default(vault):
        return base
    return base / vault


def vault_milvus_collection(config: Config, vault: str) -> str:
    if is_default(vault):
        return config.milvus_collection
    return f"{config.milvus_collection}__{vault}"


def list_vaults(config: Config) -> list[str]:
    """Discover known vaults by scanning notes_dir for subdirs that look like vaults.

    Heuristic: a vault subdir is any direct child of notes_dir that is NOT a year-shaped
    folder (`2026`, `2025`, etc.) and is NOT one of the bookkeeping files (`index.md`,
    `log.md`, `.understand-anything`).
    """
    found = {DEFAULT_VAULT}
    if config.notes_dir.exists():
        for child in config.notes_dir.iterdir():
            if not child.is_dir():
                continue
            n = child.name
            if n.isdigit() and len(n) == 4:    # year folder, default vault
                continue
            if n.startswith(".") or n in {"_archive", "_attachments"}:
                continue
            found.add(n)
    return sorted(found)
