"""CLI query output — pointer & synthesis Q&A over the Milvus-indexed notes.

Pointer mode: returns ranked hits with note paths + snippets (no LLM call).
Synthesis mode: retrieves, then asks the LLM to compose a cited answer.
"""
from __future__ import annotations

from ..core.config import Config
from ..core.llm import chat
from ..core.registry import register_output


SYNTHESIS_SYSTEM = """You are a librarian for a personal wiki of distilled notes that the
user has built from things they've read, watched, or saved. Answer the user's question
using ONLY the notes provided below.

Rules:
- Cite notes with [n] markers matching the numbered list in the context.
- If the notes don't contain the answer, say so plainly. Don't invent or guess.
- Prefer specifics from the notes (numbers, quotes, names) over generic prose.
- One concise answer, no preamble."""


def _hit_field(hit: dict, key: str, default: str = "") -> str:
    """Tolerate Milvus result shapes that wrap fields in 'entity' or expose them flat."""
    entity = hit.get("entity", {})
    if isinstance(entity, dict) and key in entity:
        return str(entity[key])
    if key in hit:
        return str(hit[key])
    return default


def pointer_query(config: Config, question: str, top_k: int | None = None, vault: str = "default") -> list[dict]:
    """Top-k semantic search in a single vault. No LLM call."""
    from ..knowledge.milvus_index import search
    return search(config, query=question, top_k=top_k or config.top_k, vault=vault)


def synthesis_query(config: Config, question: str, top_k: int | None = None, vault: str = "default") -> tuple[str, list[dict]]:
    hits = pointer_query(config, question, top_k=top_k, vault=vault)
    if not hits:
        return (
            "(no relevant notes found — has the index been populated? "
            "try `wikillm backfill` or run `wikillm process` after enqueuing some sources)",
            [],
        )

    blocks = []
    for i, h in enumerate(hits, 1):
        title = _hit_field(h, "title", "(no title)")
        path = _hit_field(h, "note_path")
        text = _hit_field(h, "text")
        blocks.append(f"[{i}] {title} ({path})\n{text}")
    context = "\n\n".join(blocks)

    answer = chat(
        config,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": f"Question: {question}\n\nNotes:\n{context}"},
        ],
        model=config.model_synthesis,
        temperature=0.1,
        max_tokens=1500,
    )
    return answer, hits


class CliQueryOutput:
    """Registered for discoverability via `wikillm list-plugins`.

    Functionality is invoked imperatively via the `wikillm ask` CLI command rather
    than via serve() — `serve()` is for long-running outputs (bots, web UIs).
    """
    name = "cli-query"

    def serve(self, config: Config, registry) -> None:
        raise RuntimeError("cli-query is invoked imperatively via `wikillm ask`, not serve().")


register_output(CliQueryOutput())
