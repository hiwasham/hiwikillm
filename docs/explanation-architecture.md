# Architecture Explanation

`wikillm` is built around one narrow idea: every source becomes text, every text item becomes one structured Markdown note, and every note becomes both a human-readable vault entry and machine-searchable retrieval data.

The code keeps that flow small by splitting behavior into three plugin layers.

```text
RawItem
  |
  v
Input adapter
  |
  v
source_text
  |
  v
Knowledge stages, in import order
  |
  +--> Markdown note in notes/
  +--> vectors in Milvus
  +--> entities in SQLite
  +--> log.md entry
  |
  v
Outputs and scanners
```

## The Problem

A personal knowledge tool has many edges:
- Sources arrive from URLs, videos, repos, PDFs, plain text, feeds, email, and Drive.
- Storage needs to serve both 
	- humans and 
	- retrieval systems like claude code or alphaclaw.
- The user needs 
	- quick capture through Telegram 
		- [[Andrej Karpathy’s LLM Wiki hiwa claude code Commands serve telegram-bot hiwikillmbot]]
	- and batch capture through scanners.
		- [[deeplearning.ai claude hiwa knowledge management crewai deeplearningai crew resource catalog manager]]
- The LLM prompt output has to stay stable because downstream tools parse it.

Without a narrow architecture, each new source or output would push special cases into the core pipeline.

## The Approach

### Inputs Only Fetch Text
Input adapters live in `wikillm/inputs/`. 
They answer two questions:
1. Does this adapter handle the item?
2. What text should the pipeline distill?

The adapter does not write notes, index chunks, or answer questions. That keeps source-specific complexity away from the knowledge layer.

Active adapters:
- `url`: fetches HTTP/HTTPS content and extracts text from HTML.
- `youtube`: uses `yt-dlp` to fetch metadata and subtitles.
- `github`: uses GitHub's REST API to fetch repo metadata, README, and top-level tree.
- `pdf`: extracts local PDF text with `pypdf`.
- `text`: passes inline `RawItem.raw_payload` or `source_ref` through as text.
`notebooklm.py` exists as a documented stub. It is not imported in `wikillm/inputs/__init__.py`, so it is not registered.

### `/knowledge:` Knowledge Stages Run In Order
Knowledge stages live in `wikillm/knowledge/`. 

The order is defined by imports in `wikillm/knowledge/__init__.py`:

```text
llm-distill
markdown-vault
milvus-index
entity-index
log-writer
```

That order matters:
- `llm-distill` 
	- must run before anything can write or index a note.
- `markdown-vault` 
	- must run before Milvus indexing 
		- because `note_path` is part of indexed metadata.
- `entity-index` 
	- reads the final note Markdown 
	- and stores `[[wikilinks]]`.
- `log-writer` records the final artifact counts.

The trade-off is that plugin order is simple but implicit. Adding a stage is easy, but a misplaced import can break downstream assumptions.

### /outputs : outputs Are User Interfaces
Outputs live in `wikillm/outputs/`.

- `cli-query` 
	- is registered so it appears in plugin listings, but its actual interface is `wikillm ask`.
- `telegram-bot` 
	- is a blocking long-poll loop that handles capture, retrieval, review, and stats commands.
	- [[Andrej Karpathy’s LLM Wiki hiwa claude code Commands serve telegram-bot hiwikillmbot]]

The Telegram bot also drains one inbox item between polling cycles. 
That is a deliberate operational choice: the bot owns Milvus writes so cron scanners can enqueue SQLite work without competing for the Milvus Lite file lock.

```text
cron / manual scanners
  |
  v
SQLite inbox only
  |
  v
telegram-bot process loop
  |
  v
Milvus + notes + entity DB
```

## Vaults

A vault partitions the knowledge base by domain. The default vault preserves the old layout:

```text
notes/YYYY/MM/<slug>.md
sources/
todos/
Milvus collection: wikillm_notes
```

Named vaults nest under the vault name:

```text
notes/<vault>/YYYY/MM/<slug>.md
sources/<vault>/
todos/<vault>/
Milvus collection: wikillm_notes__<vault>
```

`list_vaults()` discovers vaults by scanning direct children of `notes/` and ignoring year-shaped folders such as `2026`.

The trade-off is pragmatic discovery over explicit configuration. It works well for a personal vault, but renaming directories can change discovered vaults.

## Note Schema Is A Contract

The distillation prompt requires every note to contain:

- YAML frontmatter with `title`, `source`, `kind`, `captured_at`, `page_type`, and `tags`.
- `## TL;DR`
- `## Key claims & findings`
- `## Entities & links`
- `## Open questions`
- `## Source`

This is not just formatting. Other features depend on it:

- `build-index` reads frontmatter and tags.
- `build-todos` extracts `## Open questions`.
- `entity-index` extracts `[[wikilinks]]`.
- Retrieval stores title, source, kind, and path metadata.

Changing the note schema should be treated as a migration.

## State And Failure Boundaries

`wikillm` keeps source code and private state separate:

```text
committed:
  wikillm/
  config.example.toml
  docs/
  systemd/

local only:
  config.toml
  data/
  notes/
  sources/
  todos/
```

This protects the personal wiki, tokens, and runtime databases from being committed.

Processing failures are captured at the inbox level. `process` marks a row as `error` and stores the exception text. `distill` is immediate and raises through the CLI instead of recording an inbox row.

## Why Not One Big Pipeline Class

The plugin registry keeps the core small:

```text
register_input()
register_knowledge_stage()
register_output()
load_all()
detect_input()
```

The core does not know about YouTube, Milvus, Telegram, or feed parsing. It knows how to load plugins and push a `RawItem` through registered behavior.

The trade-off is that imports have side effects. A plugin is registered because its module was imported. This is simple for a small personal project, but it means documentation and tests should verify `wikillm list-plugins` after adding plugins.

## Operational Trade-Offs

| Choice | Benefit | Cost |
| --- | --- | --- |
| Markdown notes as primary artifact | Human-readable, Obsidian-friendly, git-copyable if desired | LLM output schema needs discipline |
| SQLite inbox | Simple, durable local queue | No distributed worker coordination |
| Milvus Lite | Local semantic search without a server | Single-writer file lock risk |
| Plugin imports for registration | Very small extension protocol | Import order and side effects matter |
| Telegram bot drains queue | One long-running owner for Milvus writes | Throughput is intentionally low |
| Vault discovery from folders | No extra config needed | Folder structure becomes behavior |

## Known Architecture Gaps

- There are no automated tests in the repo today.
- `scripts/smoke_test.sh` calls the old `distill-url` command and needs updating to `distill`.
- `email_imap.py` and `notebooklm.py` are stubs.
- `_detect_kind()` may produce `file`, but no `file` input adapter is registered.
- README phase language is stale relative to the current code.
