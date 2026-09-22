# LLM Project Story Brief

Rewrite `PROJECT_STORY.md` into a concise product narrative for future agents or project docs.

Use these sources first:

- `/root/projects/hiwikillm/README.md`
- `/root/projects/hiwikillm/AGENTS.md`
- `/root/projects/hiwikillm/CLAUDE.md`
- `/root/projects/hiwikillm/config.example.toml`
- `/root/projects/hiwikillm/wikillm/`
- `/root/.gstack-brain-worktree/projects/hiwikillm.md` if additional historical context is needed

Treat these as lower-trust:

- `project-recovery-transcripts.html`
- `project-recovery-evidence.json`
- Any transcript matches from unrelated OpenClaw, saveme, or generic `llm`/`bot` sessions

Important facts:

- Canonical root: `/root/projects/hiwikillm`
- Python package: `/root/projects/hiwikillm/wikillm`
- Product: personal wiki-LLM that distills inputs into structured Markdown notes and indexes them for cited Q&A
- Main runtime state: `config.toml`, `data/`, `notes/`, `sources/`, `todos/`
- Main interfaces: CLI and private Telegram bot
- Architecture: plugin-style inputs, ordered knowledge stages, output adapters, scanners
- Key operational risk: Milvus Lite single-writer behavior; avoid multiple bot/indexing processes

Desired output:

- What the project is
- Who it serves
- Current capabilities
- Important constraints and private files
- Known gaps or stale docs
- Next useful build packet
