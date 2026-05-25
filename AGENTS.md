# AGENTS.md — wikillm

You're an agent operating inside the `wikillm` workspace. This file tells you how to behave here. (Claude Code reads `CLAUDE.md`; both point to this for the substantive content.)

## What this project is

wikillm is a **personal wiki-LLM** following Karpathy's pattern. Inputs (URLs, YouTube, GitHub repos, PDFs, free text) get distilled by an LLM into structured Markdown notes; those notes are indexed in Milvus for cited Q&A; outputs include a Telegram bot, CLI ask, and auto-generated `index.md` + `todos/`.

Repo: https://github.com/hiwasham/hiwikillm  
Bot: `@hiwikillmbot` (Telegram)

## Layout — three-layer plugin architecture

| Path | What lives here |
|---|---|
| `wikillm/core/` | shared types, plugin registry, config, SQLite inbox queue, gateway LLM client |
| `wikillm/inputs/` | source adapters (one file per kind: url, youtube, github, pdf, text) |
| `wikillm/knowledge/` | pipeline stages (llm-distill → markdown-vault → milvus-index → entity-index → log-writer) |
| `wikillm/outputs/` | consumers (cli-query, telegram-bot) |
| `wikillm/scanners/` | push-discovery (drive_sources, build_index, build_todos) |
| `notes/` | distilled output — *gitignored*; this is the user's personal wiki |
| `sources/` | raw drops awaiting `wikillm scan` — *gitignored* |
| `data/` | SQLite inbox, Milvus DB, entity DB — *gitignored* |
| `todos/` | extracted open questions per note (Phase D) — *gitignored* |
| `config.toml` | runtime config — *gitignored, contains secrets* |
| `config.example.toml` | template for new clones |

## Adding a new plugin — the seam that matters

Each layer is a directory; plugins self-register on import. To add a new one:

1. **New input** (e.g. RSS, subreddit, NotebookLM connector): write `inputs/<name>.py` with `name`, `matches(ref, *, kind_hint=None) -> bool`, and `fetch(config, item) -> str`. End the file with `register_input(YourInput())`. Add `from . import <name>` to `inputs/__init__.py`.
2. **New knowledge stage** (e.g. entity canonicalization, dashboard data): write `knowledge/<name>.py` with `name` and `run(config, state) -> None`. Register with `register_knowledge_stage`. Add import in `knowledge/__init__.py` — *order matters* (stages run in import order).
3. **New output** (e.g. weekly digest email, podcast generator): write `outputs/<name>.py` with `name` and `serve(config, registry) -> None`. Register and import.

That's the whole protocol. No core changes needed.

## Conventions

- **LLM calls** go through `core.llm.chat()` — it retries 429/5xx with exponential backoff.
- **Secrets**: never duplicate in code or `config.toml`. Use `token_path` (dotted path into `~/.openclaw/openclaw.json`) or env vars.
- **SQLite/DB state** lives in `data/`. Never commit it.
- **Distilled notes** are Markdown with YAML frontmatter. The schema is downstream-load-bearing — `entity-index`, `build-index`, `build-todos`, and Understand-Anything's `/understand-knowledge` all depend on it. Required fields: `title`, `source`, `kind`, `captured_at`, `page_type`, `tags`. Required sections: `## TL;DR`, `## Key claims & findings`, `## Entities & links` (with `[[wikilinks]]`), `## Open questions`, `## Source`.
- **LLM prompts** are inline in their stage module (e.g. `knowledge/llm_distill.py::USER_TEMPLATE`). Keep them in code, not external files.

## Do NOT

- Don't modify the running Telegram bot's behavior without restarting it — Python caches modules.
- Don't share `data/milvus.db` with another process — Milvus Lite uses single-writer file locks. Running two `wikillm serve telegram-bot` instances at once is a guaranteed deadlock.
- Don't `git add` `config.toml`, `data/`, `notes/`, `sources/`, or `todos/`. They're gitignored.
- Don't `pip install --break-system-packages` casually — use a venv when available. The Pi accepts `--break-system-packages` only because no venv was installable at project start.

## Common operations

```bash
python3 -m wikillm list-plugins         # show all registered plugins per layer
python3 -m wikillm enqueue <ref>        # add a URL/path/text to the inbox
python3 -m wikillm process [--once]     # drain inbox (distill → vault → index → log)
python3 -m wikillm distill <ref>        # one-shot, bypass queue
python3 -m wikillm ask <question>       # synthesis Q&A (LLM-composed, cited)
python3 -m wikillm find <query>         # pointer Q&A (top-k, no LLM)
python3 -m wikillm scan                 # enqueue new files in sources/
python3 -m wikillm build-index          # write notes/index.md
python3 -m wikillm build-todos          # write todos/index.md
python3 -m wikillm entities --limit 50  # frequency-ranked [[entities]] across vault
python3 -m wikillm backfill             # re-index all notes/ into Milvus
python3 -m wikillm backfill-entities    # re-extract [[entities]] from all notes
python3 -m wikillm serve telegram-bot   # run the bot (blocks)
python3 -m wikillm stats                # inbox counts by status
```

## Where to look when stuck

- Full plan + roadmap: `/home/miraddo/.claude/plans/i-have-obsidian-on-refactored-cook.md`
- Architecture decisions + history: `/home/miraddo/.claude/projects/-home-miraddo/memory/MEMORY.md`
- Bot log (when running under tmux): `bot.log` in workspace root
- Gateway reality (which LLM endpoint actually works): see memory `reference_llm_gateway`
