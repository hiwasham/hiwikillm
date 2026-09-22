# wikillm

`wikillm` is a personal wiki-LLM. It captures source material, distills each item into a structured Markdown note, indexes the notes for retrieval, and exposes the knowledge base through CLI commands and a private Telegram bot.

Sources can come from URLs, YouTube videos, GitHub repos, PDFs, free text, local source folders, and configured feeds. Notes are written to `notes/`, indexed in Milvus Lite, and enriched with `[[wikilink]]` entity data.

## Current Capabilities

- Capture immediately with `python3 -m wikillm distill <ref>`.
- Queue captures with `enqueue` and drain them with `process`.
- Scan `sources/` and feed subscriptions into the queue.
- Ask pointer or synthesized questions over indexed notes.
- Build human-facing `notes/index.md` and `todos/index.md`.
- Track and canonicalize `[[entities]]`.
- Review old notes with a simple spaced-repetition schedule.
- Serve a private Telegram bot with capture, ask, find, review, and stats commands.
- Partition notes into named vaults.

## Architecture

The package is split into small plugin layers:

| Path | Purpose |
| --- | --- |
| `wikillm/core/` | Shared types, registry, config, SQLite queue, LLM gateway, vault helpers. |
| `wikillm/inputs/` | Source adapters: URL, YouTube, GitHub, PDF, text. |
| `wikillm/knowledge/` | Ordered pipeline stages: distill, write Markdown, index Milvus, index entities, log. |
| `wikillm/outputs/` | User-facing interfaces: CLI query and Telegram bot. |
| `wikillm/scanners/` | Source folder, feed, index, todos, review, and canonicalization utilities. |

The core pipeline is intentionally small:

```text
RawItem -> input adapter -> source_text -> knowledge stages -> notes/indexes -> outputs
```

## Quick Start

Install dependencies:

```bash
python3 -m pip install --user -r requirements.txt
```

Create local config:

```bash
cp config.example.toml config.toml
```

Edit `config.toml` so `[gateway].openclaw_config`, `[gateway].token_path`, and optional Telegram settings point at your local secrets.

Verify plugin loading:

```bash
python3 -m wikillm list-plugins
```

Capture one source:

```bash
python3 -m wikillm distill https://example.com/
```

Ask over indexed notes:

```bash
python3 -m wikillm ask "What is this source about?"
```

## Common Commands

```bash
python3 -m wikillm enqueue <ref>        # add URL/path/text to the inbox
python3 -m wikillm process [--once]     # drain inbox through the pipeline
python3 -m wikillm distill <ref>        # process one source immediately
python3 -m wikillm ask <question>       # synthesized cited Q&A
python3 -m wikillm ask <question> --mode pointer
python3 -m wikillm scan                 # enqueue new files from sources/
python3 -m wikillm scan-feeds           # poll configured RSS/Atom feeds
python3 -m wikillm build-index          # write notes/index.md
python3 -m wikillm build-todos          # write todos/index.md
python3 -m wikillm entities --limit 50  # list frequent [[entities]]
python3 -m wikillm backfill             # re-index notes into Milvus
python3 -m wikillm backfill-entities    # re-extract note entities
python3 -m wikillm review               # show notes due for rereading
python3 -m wikillm serve telegram-bot   # run the Telegram bot
```

## Documentation

Start here:

- [Getting Started With wikillm](docs/tutorial-getting-started.md)
- [How to Capture Sources and Query Notes](docs/how-to-capture-and-query.md)
- [How to Use wikillm With Obsidian](docs/how-to-use-with-obsidian.md)
- [How to Sync wikillm Notes With GBrain](docs/how-to-sync-with-gbrain.md)
- [How to Add a Plugin](docs/how-to-add-a-plugin.md)
- [CLI Reference](docs/reference-cli.md)
- [Configuration Reference](docs/reference-configuration.md)
- [Architecture Explanation](docs/explanation-architecture.md)

Project recovery and operating docs are also available in [docs/index.md](docs/index.md).

## Private State

These paths are local and gitignored:

- `config.toml`
- `data/`
- `notes/`
- `sources/`
- `todos/`

Do not commit personal notes, Milvus/SQLite databases, Telegram tokens, or gateway credentials.

## Operational Notes

- LLM calls go through `wikillm/core/llm.py::chat()`.
- Note schema is a contract. `entity-index`, `build-index`, `build-todos`, and retrieval depend on the generated frontmatter and sections.
- Milvus Lite should be treated as single-writer. Do not run multiple bot or indexing processes against the same `data/milvus.db`.
- `notebooklm.py` and `email_imap.py` are documented stubs.
- `scripts/smoke_test.sh` is stale and still calls `distill-url`; use `distill` until that script is updated.
