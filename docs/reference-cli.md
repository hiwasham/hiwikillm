# CLI Reference

`python3 -m wikillm` is the main command surface for capture, processing, retrieval, indexing, and maintenance.

All commands load `config.toml` unless noted. Commands that call the full pipeline also call `load_all()`, which imports input, knowledge, and output plugins so they self-register.

## Commands

| Command | Purpose |
| --- | --- |
| `enqueue <ref>` | Add a URL, path, or text snippet to the SQLite inbox. |
| `process [--once]` | Drain pending inbox items through input fetch and all knowledge stages. |
| `distill <ref>` | Process one item immediately without queueing it. |
| `ask <question>` | Query indexed notes with pointer or synthesis mode. |
| `scan` | Enqueue supported files from `sources/` or vault-specific source folders. |
| `scan-feeds` | Poll configured RSS/Atom feeds and enqueue new entries. |
| `build-index` | Write a Markdown table of contents for notes. |
| `build-todos` | Extract `## Open questions` into a todos index. |
| `backfill` | Re-index existing notes into Milvus. |
| `backfill-entities` | Re-extract `[[wikilinks]]` from existing notes into SQLite. |
| `entities` | Print frequency-ranked wiki entities. |
| `canonicalize` | Propose or apply LLM-based entity-name canonicalization. |
| `review` | Show notes due for spaced-repetition rereading. |
| `reviewed <slug>` | Mark one note as reread. |
| `vaults` | List discovered vaults and note counts. |
| `list-plugins` | Print registered inputs, stages, and outputs. |
| `stats` | Print inbox counts by status. |
| `serve <output-name>` | Run a blocking output adapter such as `telegram-bot`. |

## Capture And Processing

### `enqueue`

```bash
python3 -m wikillm enqueue <ref> [--kind KIND] [--vault NAME]
```

Adds one row to `data/inbox.db`.

Arguments:

- `ref`: URL, file path, or free text.
- `--kind`: optional input kind. If omitted, the CLI detects `youtube`, `github`, `url`, `pdf`, `file`, or `text`.
- `--vault`: vault name. Defaults to `default`.

Output:

```text
enqueued #12 kind=url vault=default
```

Notes:

- Inline text is stored in `raw_payload`.
- For non-text refs, `raw_payload` is `NULL`.
- `file` is detected for non-PDF local files, but there is no registered `file` input adapter. Use `--kind text` for local text files or drop `.txt`/`.md` files into `sources/` and run `scan`.

### `process`

```bash
python3 -m wikillm process [--once]
```

Claims pending inbox rows in FIFO order and runs:

```text
input adapter -> llm-distill -> markdown-vault -> milvus-index -> entity-index -> log-writer
```

Options:

- `--once`: process one row and exit.

State changes:

- Marks rows as `processing`, then `done` or `error`.
- Writes notes under `notes/`.
- Writes Milvus chunks to `data/milvus.db`.
- Writes entity rows to `data/entities.db`.
- Appends to `notes/log.md` or `notes/<vault>/log.md`.

### `distill`

```bash
python3 -m wikillm distill <ref> [--kind KIND] [--vault NAME]
```

Runs one item through the full pipeline without inserting an inbox row. Prints the generated note path.

## Retrieval

### `ask`

```bash
python3 -m wikillm ask <question> [--mode pointer|synthesis] [--top-k N] [--vault NAME]
```

Modes:

- `pointer`: returns Milvus hits with note paths and snippets. No LLM call.
- `synthesis`: retrieves hits, then calls the synthesis model to answer with source markers. This is the default.

Options:

- `--top-k`: overrides `[milvus].top_k`.
- `--vault`: searches one vault. Defaults to `default`.

If no hits exist, synthesis mode tells you to run `wikillm backfill` or process sources first.

## Discovery And Generated Vault Files

### `scan`

```bash
python3 -m wikillm scan [--vault NAME]
```

Scans `sources/` for supported files and enqueues new source refs.

Supported suffixes:

| Suffix | Enqueued kind | Behavior |
| --- | --- | --- |
| `.pdf` | `pdf` | Enqueues the path. |
| `.txt` | `text` | Reads file content into `raw_payload`. |
| `.md` | `text` | Reads file content into `raw_payload`. |
| `.url` | `url` | Reads the first non-empty URL line, including `URL=...` files. |

Without `--vault`, `scan` scans all discovered vaults. Named vaults use `sources/<vault>/`.

### `scan-feeds`

```bash
python3 -m wikillm scan-feeds
```

Polls `[feeds].subscriptions` from `config.toml`.

Each feed entry supports:

- `url`: RSS or Atom feed URL.
- `kind`: input kind for enqueued entries. Defaults to `url`.
- `vault`: target vault. Defaults to `default`.

Seen entries are stored in `data/feed_seen.db`.

### `build-index`

```bash
python3 -m wikillm build-index [--vault NAME] [--all]
```

Writes `notes/index.md` for the default vault or `notes/<vault>/index.md` for a named vault. The index includes notes by tag, all notes, and top entities.

### `build-todos`

```bash
python3 -m wikillm build-todos [--vault NAME] [--all]
```

Extracts bullet items from each note's `## Open questions` section and writes `todos/index.md` or `todos/<vault>/index.md`.

## Backfills And Entity Maintenance

### `backfill`

```bash
python3 -m wikillm backfill [--vault NAME] [--all]
```

Re-indexes existing Markdown notes into the vault's Milvus collection. It skips `index.md` and `log.md`.

### `backfill-entities`

```bash
python3 -m wikillm backfill-entities [--vault NAME] [--all]
```

Re-extracts `[[wikilinks]]` from notes into `data/entities.db`.

### `entities`

```bash
python3 -m wikillm entities [--limit N] [--vault NAME]
```

Prints entity names by number of distinct notes. Without `--vault`, it sums across all vaults.

### `canonicalize`

```bash
python3 -m wikillm canonicalize [--apply]
```

Builds `data/canonical_entities.json` by asking the LLM to map variant entity names to canonical names.

Behavior:

- Without `--apply`, saves or updates the mapping only.
- With `--apply`, rewrites note wikilinks on disk.

After `--apply`, run:

```bash
python3 -m wikillm backfill --all
python3 -m wikillm backfill-entities --all
```

## Review

### `review`

```bash
python3 -m wikillm review [--count N]
```

Shows notes due for rereading. The schedule is one day for never-reviewed notes, then intervals of 1, 3, 7, 14, 30, 90, 180, and 365 days.

### `reviewed`

```bash
python3 -m wikillm reviewed <slug-fragment>
```

Marks exactly one matching note as reviewed. If zero or multiple notes match, the command exits with an error.

## Introspection And Outputs

### `vaults`

```bash
python3 -m wikillm vaults
```

Discovers vaults by scanning direct children of `notes/`. Year-shaped folders such as `2026` belong to the default vault and are not treated as vaults.

### `list-plugins`

```bash
python3 -m wikillm list-plugins
```

Prints registered inputs, knowledge stages in import order, and outputs.

Current registered plugins:

```text
inputs:
  - github
  - pdf
  - text
  - url
  - youtube
knowledge stages (in order):
  - llm-distill
  - markdown-vault
  - milvus-index
  - entity-index
  - log-writer
outputs:
  - cli-query
  - telegram-bot
```

### `stats`

```bash
python3 -m wikillm stats
```

Prints inbox counts grouped by status.

### `serve`

```bash
python3 -m wikillm serve telegram-bot
```

Runs the named output adapter. `telegram-bot` blocks forever and long-polls Telegram.

`cli-query` is registered for discoverability but cannot be served; use `wikillm ask`.

## Known CLI Documentation Gaps

- `scripts/smoke_test.sh` calls `python3 -m wikillm distill-url`, but the current CLI command is `distill`.
- `_detect_kind()` can return `file` for non-PDF local files, but there is no registered `file` adapter. Use `--kind text` or `scan` for text files.
