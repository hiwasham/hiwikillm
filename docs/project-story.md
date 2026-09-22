# Project Story: hiwikillm

## Product Narrative

`hiwikillm` is a personal wiki-LLM system. It captures source material from URLs, YouTube links, GitHub repos, PDFs, free text, feeds, email, and local source folders; distills each item with an LLM into structured Markdown notes; indexes the notes in Milvus for retrieval; and exposes the knowledge base through CLI commands and a private Telegram bot.

The canonical project root is `/root/projects/hiwikillm`. The actual Python package is `/root/projects/hiwikillm/wikillm`.

## Current Capabilities

- CLI capture, processing, retrieval, entity, review, and backfill commands.
- Input adapters for URL, YouTube, GitHub, PDF, and text.
- Knowledge stages for LLM distillation, Markdown vault writing, Milvus indexing, entity indexing, and log writing.
- Multi-vault note and collection support.
- Private Telegram bot with capture, ask, find, review, reviewed, stats, and help commands.
- Systemd service files for bot operation and rclone/Drive sync.

## Recovery Notes

- The gstack brain note at `/root/.gstack-brain-worktree/projects/hiwikillm.md` is supporting context, not the project root.
- The raw transcript/evidence files include noisy matches from unrelated sessions. Prefer `README.md`, `AGENTS.md`, `CLAUDE.md`, `config.example.toml`, and `wikillm/` as source of truth.

## Next Build Packet

Review and commit the curated recovery docs, reconcile stale README phase language with the current code, and add focused tests around plugin registration, vault-aware queueing, and Telegram queue draining.
