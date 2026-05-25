"""Milvus indexing knowledge stage — chunks DistilledNotes, embeds, upserts.

Uses pymilvus (Milvus Lite via local .db file) + fastembed (ONNX embeddings, no torch).
Both heavy imports are lazy so Phase A still works if these packages are missing.
"""
from __future__ import annotations

import re
from typing import Any

from ..core.config import Config
from ..core.registry import register_knowledge_stage
from ..core.types import PipelineState


_MILVUS_CLIENT: Any = None
_EMBED_MODEL: Any = None
_LOADED_COLLECTIONS: set[str] = set()


def _get_milvus_client(config: Config, collection: str | None = None):
    """Return the singleton client, ensuring `collection` exists + is loaded.

    `collection` defaults to the default-vault collection. Pass an explicit name
    when querying or indexing a non-default vault.
    """
    global _MILVUS_CLIENT
    if _MILVUS_CLIENT is None:
        from pymilvus import MilvusClient
        _MILVUS_CLIENT = MilvusClient(uri=config.milvus_uri)
    coll = collection or config.milvus_collection
    if coll not in _LOADED_COLLECTIONS:
        if not _MILVUS_CLIENT.has_collection(coll):
            _MILVUS_CLIENT.create_collection(
                collection_name=coll,
                dimension=config.milvus_embedding_dim,
                metric_type="COSINE",
                auto_id=True,
                enable_dynamic_field=True,
            )
        _MILVUS_CLIENT.load_collection(collection_name=coll)
        _LOADED_COLLECTIONS.add(coll)
    return _MILVUS_CLIENT


def _get_embed_model(config: Config):
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        from fastembed import TextEmbedding
        _EMBED_MODEL = TextEmbedding(model_name=config.embedding_model)
    return _EMBED_MODEL


def embed_one(config: Config, text: str) -> list[float]:
    model = _get_embed_model(config)
    vecs = list(model.embed([text]))
    return vecs[0].tolist()


def embed_batch(config: Config, texts: list[str]) -> list[list[float]]:
    model = _get_embed_model(config)
    return [v.tolist() for v in model.embed(texts)]


def _chunk(text: str, size: int, overlap: int) -> list[str]:
    """Sliding-window chunks. Prefers paragraph-boundary cuts in the upper half of the window."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    chunks: list[str] = []
    i = 0
    while i < len(text):
        end = min(i + size, len(text))
        if end < len(text):
            nl = text.rfind("\n\n", i + size // 2, end)
            if nl != -1:
                end = nl
        piece = text[i:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        i = max(i + 1, end - overlap)
    return chunks


def _strip_frontmatter(md: str) -> str:
    return re.sub(r"^---\n.*?\n---\n+", "", md, count=1, flags=re.DOTALL)


def index_markdown(
    config: Config,
    *,
    note_path: str,
    title: str,
    kind: str,
    source_ref: str,
    markdown: str,
    captured_at: str,
    vault: str = "default",
) -> int:
    """Re-index one note. Deletes prior chunks for this note_path, then inserts fresh ones."""
    from ..core.vaults import vault_milvus_collection
    coll = vault_milvus_collection(config, vault)
    client = _get_milvus_client(config, coll)
    body = _strip_frontmatter(markdown)
    chunks = _chunk(body, config.chunk_size_chars, config.chunk_overlap_chars)
    if not chunks:
        return 0

    try:
        client.delete(collection_name=coll, filter=f'note_path == "{note_path}"')
    except Exception:
        pass

    vectors = embed_batch(config, chunks)
    rows = [
        {
            "vector": v,
            "note_path": note_path,
            "title": title,
            "kind": kind,
            "source_ref": source_ref,
            "chunk_idx": idx,
            "text": chunk,
            "captured_at": captured_at,
            "vault": vault,
        }
        for idx, (chunk, v) in enumerate(zip(chunks, vectors))
    ]
    client.insert(collection_name=coll, data=rows)
    return len(rows)


def search(config: Config, *, query: str, top_k: int, vault: str = "default") -> list[dict]:
    """Return top-k hits from the given vault's collection."""
    from ..core.vaults import vault_milvus_collection
    coll = vault_milvus_collection(config, vault)
    client = _get_milvus_client(config, coll)
    vec = embed_one(config, query)
    results = client.search(
        collection_name=coll,
        data=[vec],
        limit=top_k,
        output_fields=["note_path", "title", "kind", "source_ref", "chunk_idx", "text", "captured_at", "vault"],
    )
    if not results:
        return []
    return list(results[0])


def collection_stats(config: Config, vault: str = "default") -> dict:
    from ..core.vaults import vault_milvus_collection
    coll = vault_milvus_collection(config, vault)
    client = _get_milvus_client(config, coll)
    if not client.has_collection(coll):
        return {"exists": False}
    n = client.get_collection_stats(collection_name=coll)
    return {"exists": True, "stats": n}


class MilvusIndexStage:
    name = "milvus-index"

    def run(self, config: Config, state: PipelineState) -> None:
        if state.distilled is None or state.distilled.note_path is None:
            return
        n = index_markdown(
            config,
            note_path=state.distilled.note_path,
            title=state.distilled.title,
            kind=state.item.kind,
            source_ref=state.item.source_ref,
            markdown=state.distilled.markdown,
            captured_at=state.distilled.captured_at.isoformat(),
            vault=state.item.vault,
        )
        state.artifacts["milvus_chunks"] = n


register_knowledge_stage(MilvusIndexStage())
