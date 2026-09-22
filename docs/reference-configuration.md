# Configuration Reference

`wikillm` reads runtime configuration from `config.toml` in the project root. The committed `config.example.toml` is the template.

Do not commit `config.toml`. It contains local paths and may contain Telegram or gateway secrets.

## Loading Behavior

`wikillm/core/config.py::load_config()`:

1. Resolves the project root.
2. Opens `config.toml`.
3. Opens the configured OpenClaw JSON file.
4. Resolves the gateway token through the dotted `token_path`.
5. Returns a frozen `Config` dataclass.

Relative paths in config are resolved against the project root.

## `[paths]`

```toml
[paths]
notes_dir = "notes"
sources_dir = "sources"
inbox_db = "data/inbox.db"
```

| Key | Type | Default in example | Effect |
| --- | --- | --- | --- |
| `notes_dir` | path string | `notes` | Base directory for distilled Markdown notes. |
| `sources_dir` | path string | `sources` | Base directory scanned by `wikillm scan`. |
| `inbox_db` | path string | `data/inbox.db` | SQLite inbox path. |

For named vaults, `notes_dir` and `sources_dir` are nested by vault name:

```text
notes/<vault>/...
sources/<vault>/...
```

The default vault writes directly under `notes/` and `sources/`.

## `[gateway]`

```toml
[gateway]
base_url = "https://api.freemodel.dev/v1"
openclaw_config = "/home/YOU/.openclaw/openclaw.json"
token_path = "models.providers.freemodel.apiKey"
```

| Key | Type | Effect |
| --- | --- | --- |
| `base_url` | URL string | OpenAI-compatible base URL. `wikillm` calls `<base_url>/chat/completions`. |
| `openclaw_config` | path string | JSON file that holds the gateway token. |
| `token_path` | dotted path string | Path inside the JSON file used to read the token. |

Gateway calls go through `wikillm/core/llm.py::chat()`.

Retry behavior:

- Retries HTTP `429`, `500`, `502`, `503`, and `504`.
- Retries network errors from `httpx`.
- Uses exponential backoff with defaults of 2, 4, and 8 seconds.
- Raises immediately for non-retryable 4xx responses.

## `[models]`

```toml
[models]
distill = "gpt-5.5"
distill_premium = "gpt-5.5"
synthesis = "gpt-5.5"
```

| Key | Used by | Effect |
| --- | --- | --- |
| `distill` | `llm-distill` stage | Model for source-to-note distillation. |
| `distill_premium` | config only today | Reserved model alias for future higher-cost distillation. |
| `synthesis` | `wikillm ask --mode synthesis` and Telegram `/ask` | Model for cited answer composition. |

## `[fetch]`

```toml
[fetch]
timeout_s = 30
user_agent = "wikillm/0.1 (+personal-wiki-llm)"
max_bytes = 5_000_000
```

| Key | Type | Effect |
| --- | --- | --- |
| `timeout_s` | integer seconds | Timeout for URL, GitHub, and feed fetches. |
| `user_agent` | string | User-Agent header for fetchers. |
| `max_bytes` | integer bytes | Maximum response body bytes read by the generic URL adapter. |

## `[distill]`

```toml
[distill]
max_input_chars = 80_000
```

`max_input_chars` limits source text passed to the distillation prompt. The source adapter may fetch more, but `llm-distill` truncates before calling the LLM.

## `[milvus]`

```toml
[milvus]
uri = "data/milvus.db"
collection = "wikillm_notes"
embedding_dim = 384
embedding_model = "BAAI/bge-small-en-v1.5"
chunk_size_chars = 1200
chunk_overlap_chars = 200
top_k = 6
```

| Key | Type | Effect |
| --- | --- | --- |
| `uri` | path string | Milvus Lite database path. |
| `collection` | string | Collection name for the default vault. |
| `embedding_dim` | integer | Vector dimension used when creating a collection. |
| `embedding_model` | string | `fastembed.TextEmbedding` model name. |
| `chunk_size_chars` | integer | Target Markdown chunk size after frontmatter stripping. |
| `chunk_overlap_chars` | integer | Overlap between adjacent chunks. |
| `top_k` | integer | Default retrieval count for `ask` and query helpers. |

Named vault collection names are derived as:

```text
<collection>__<vault>
```

Operational constraint: Milvus Lite uses a local file and should be treated as single-writer. Do not run multiple bot or indexing processes against the same `data/milvus.db`.

## `[telegram]`

```toml
[telegram]
bot_token = "REPLACE_WITH_YOUR_TELEGRAM_BOT_TOKEN"
owner_ids = []
poll_timeout_s = 30
```

| Key | Type | Effect |
| --- | --- | --- |
| `bot_token` | string | Telegram Bot API token. Required for `serve telegram-bot`. |
| `owner_ids` | list of integers | Optional allowlist of Telegram user IDs. Empty means open access. |
| `poll_timeout_s` | integer seconds | Long-poll timeout for `getUpdates`. |

Private deployment should set at least one `owner_ids` entry.

## `[feeds]`

```toml
[feeds]
subscriptions = []
```

Each subscription is a table-like object:

```toml
subscriptions = [
  { url = "https://example.com/feed.xml", kind = "url", vault = "default" }
]
```

Fields:

- `url`: required feed URL.
- `kind`: optional input kind for each entry link. Defaults to `url`.
- `vault`: optional target vault. Defaults to `default`.

Seen feed entries are stored in `data/feed_seen.db`.

## Local State Files

| Path | Owner | Purpose |
| --- | --- | --- |
| `data/inbox.db` | `core.queue` | Capture queue. |
| `data/milvus.db` | `knowledge.milvus_index` | Vector database. |
| `data/entities.db` | `knowledge.entity_index` | `[[wikilink]]` index. |
| `data/feed_seen.db` | `scanners.feed_watcher` | Feed deduplication. |
| `data/reviews.db` | `scanners.review` | Spaced-repetition review state. |
| `data/canonical_entities.json` | `scanners.canonicalize` | Variant-to-canonical entity map. |

All `data/` files are local runtime state and should remain uncommitted.
