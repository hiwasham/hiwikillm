# Project Story: hiwikillm

## Product Narrative

`hiwikillm` is a personal wiki-LLM system. It captures source material from URLs, YouTube links, GitHub repos, PDFs, free text, feeds, email, and local source folders; distills each item with an LLM into structured Markdown notes; indexes the notes in Milvus for retrieval; and exposes the knowledge base through CLI commands and a private Telegram bot.

The project follows a small plugin architecture:

- `wikillm/inputs/`: source adapters that fetch raw text.
- `wikillm/knowledge/`: ordered stages that distill, write, index, extract entities, and log notes.
- `wikillm/outputs/`: interactive consumers such as CLI Q&A and the Telegram bot.
- `wikillm/scanners/`: push-discovery utilities for source folders, feeds, email, index generation, todos, review, and canonicalization.

The canonical project root is `/root/projects/hiwikillm`. The actual Python package is `/root/projects/hiwikillm/wikillm`.

## Current Capabilities

- CLI commands for enqueueing, processing, one-shot distillation, plugin listing, stats, vault listing, retrieval Q&A, entity inspection, review, and backfills.
- Input adapters for URL, YouTube, GitHub, PDF, and text. `notebooklm.py` exists but is not imported in `wikillm/inputs/__init__.py`, so it is not active.
- Knowledge pipeline stages for LLM distillation, Markdown vault writing, Milvus indexing, entity indexing, and log writing.
- Multi-vault support through vault-aware queueing, note paths, and Milvus collections.
- Telegram bot output with `/capture`, `/ask`, `/find`, `/review`, `/reviewed`, `/stats`, and `/help`.
- Systemd service files for the bot and rclone/Drive sync.

## Durable Constraints

- `config.toml`, `data/`, `notes/`, `sources/`, and `todos/` are local/private and must not be committed.
- LLM calls go through `wikillm/core/llm.py::chat()`.
- Note frontmatter and required sections are downstream-load-bearing for entity extraction, index generation, todos, and retrieval.
- Milvus Lite is single-writer in practice. The Telegram bot is designed to be the sole owner of the Milvus lock while scans enqueue SQLite work.
- Plugin import order matters for knowledge stages.

## Recovery Findings

- The gstack brain note at `/root/.gstack-brain-worktree/projects/hiwikillm.md` is supporting context, not the project root.
- The generated transcript/evidence files include many noisy matches from unrelated OpenClaw and saveme sessions because the recovery query contained broad tokens such as `root`, `projects`, `llm`, and `bot`.
- Product truth should be taken from `README.md`, `AGENTS.md`, `CLAUDE.md`, `config.example.toml`, and the `wikillm/` package before relying on recovered chat snippets.

## Best Next Build Packet

Stabilize the project recovery baseline:

1. Review the generated recovery docs and commit only the curated, non-sensitive files.
2. Decide whether `/root/projects/hiwikillm` remains the canonical location or whether the copied migration target should be renamed to a cleaner path such as `/root/projects/tools-projects/hiwikillm`.
3. Run the smoke test and plugin listing from the canonical path.
4. Reconcile README status with the current code, since the README says Phase A while the package includes later phases.
5. Add focused tests around plugin registration, vault-aware queue processing, and Telegram queue draining.
