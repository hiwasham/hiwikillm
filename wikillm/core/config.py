"""Config loading. Reads config.toml from the workspace + the gateway token from openclaw.json."""
from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class Config:
    root: Path
    notes_dir: Path
    sources_dir: Path
    inbox_db: Path
    gateway_base_url: str
    gateway_token: str
    model_distill: str
    model_distill_premium: str
    model_synthesis: str
    fetch_timeout_s: int
    fetch_user_agent: str
    fetch_max_bytes: int
    distill_max_input_chars: int
    milvus_uri: str
    milvus_collection: str
    milvus_embedding_dim: int
    embedding_model: str
    chunk_size_chars: int
    chunk_overlap_chars: int
    top_k: int
    telegram_bot_token: str
    telegram_owner_ids: tuple[int, ...]
    telegram_poll_timeout_s: int


def _resolve(root: Path, value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (root / p)


def _resolve_dotted(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def load_config(workspace_root: Path | None = None) -> Config:
    root = (workspace_root or WORKSPACE_ROOT).resolve()
    with (root / "config.toml").open("rb") as f:
        raw = tomllib.load(f)

    openclaw_config_path = Path(raw["gateway"]["openclaw_config"]).expanduser()
    with openclaw_config_path.open() as f:
        openclaw = json.load(f)
    token_path = raw["gateway"].get("token_path", "gateway.auth.token")
    token = _resolve_dotted(openclaw, token_path)

    return Config(
        root=root,
        notes_dir=_resolve(root, raw["paths"]["notes_dir"]),
        sources_dir=_resolve(root, raw["paths"]["sources_dir"]),
        inbox_db=_resolve(root, raw["paths"]["inbox_db"]),
        gateway_base_url=raw["gateway"]["base_url"],
        gateway_token=token,
        model_distill=raw["models"]["distill"],
        model_distill_premium=raw["models"]["distill_premium"],
        model_synthesis=raw["models"]["synthesis"],
        fetch_timeout_s=raw["fetch"]["timeout_s"],
        fetch_user_agent=raw["fetch"]["user_agent"],
        fetch_max_bytes=raw["fetch"]["max_bytes"],
        distill_max_input_chars=raw["distill"]["max_input_chars"],
        milvus_uri=raw["milvus"]["uri"],
        milvus_collection=raw["milvus"]["collection"],
        milvus_embedding_dim=raw["milvus"]["embedding_dim"],
        embedding_model=raw["milvus"]["embedding_model"],
        chunk_size_chars=raw["milvus"]["chunk_size_chars"],
        chunk_overlap_chars=raw["milvus"]["chunk_overlap_chars"],
        top_k=raw["milvus"]["top_k"],
        telegram_bot_token=(raw.get("telegram") or {}).get("bot_token", ""),
        telegram_owner_ids=tuple((raw.get("telegram") or {}).get("owner_ids", []) or []),
        telegram_poll_timeout_s=(raw.get("telegram") or {}).get("poll_timeout_s", 30),
    )
