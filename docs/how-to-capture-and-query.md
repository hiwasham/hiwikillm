# How to Capture Sources and Query Notes

This guide shows the common ways to get source material into `wikillm` and ask questions over the resulting notes.

## Prerequisites

- `config.toml` exists and can load the gateway token.
- Dependencies from `requirements.txt` are installed.
- Milvus Lite can write to `[milvus].uri`.

Verify plugin loading:

```bash
python3 -m wikillm list-plugins
```

## Capture Immediately

Use `distill` when you want one source processed right now:

```bash
python3 -m wikillm distill https://example.com/
```

Use a vault when the source belongs to a named knowledge domain:

```bash
python3 -m wikillm distill https://example.com/ --vault research
```

Verification:

```bash
python3 -m wikillm vaults
```

You should see the vault and note count.

## Capture Through The Queue

Use `enqueue` when you want to capture now and process later:

```bash
python3 -m wikillm enqueue https://example.com/
python3 -m wikillm stats
```

Process one item:

```bash
python3 -m wikillm process --once
```

Process until the inbox is empty:

```bash
python3 -m wikillm process
```

Verification:

```bash
python3 -m wikillm stats
```

The processed row should move from `pending` to `done`, or to `error` if a stage failed.

## Capture Local Files

Drop files into `sources/`:

```text
sources/article.pdf
sources/snippet.txt
sources/page.url
```

Then run:

```bash
python3 -m wikillm scan
python3 -m wikillm process
```

Supported file types:

- `.pdf`: enqueued as `pdf`.
- `.txt`: enqueued as `text` with file content in `raw_payload`.
- `.md`: enqueued as `text` with file content in `raw_payload`.
- `.url`: enqueued as `url`; the scanner reads the first URL line.

For a named vault, drop files under:

```text
sources/<vault>/
```

Then scan only that vault:

```bash
python3 -m wikillm scan --vault research
```

## Capture Feeds

Add feed subscriptions to `config.toml`:

```toml
[feeds]
subscriptions = [
  { url = "https://example.com/feed.xml", kind = "url", vault = "default" }
]
```

Poll feeds:

```bash
python3 -m wikillm scan-feeds
python3 -m wikillm process
```

Verification:

```bash
python3 -m wikillm stats
```

Seen feed entries are stored in `data/feed_seen.db`, so repeated scans do not enqueue the same entry again.

## Query Notes Without An LLM

Use pointer mode when you want fast retrieval and source snippets:

```bash
python3 -m wikillm ask "What did I save about vector search?" --mode pointer
```

Pointer mode searches Milvus and prints ranked hits. It does not call the synthesis model.

## Query Notes With Synthesis

Use the default synthesis mode when you want a composed answer:

```bash
python3 -m wikillm ask "What did I save about vector search?"
```

Limit retrieval size:

```bash
python3 -m wikillm ask "What did I save about vector search?" --top-k 3
```

Query a named vault:

```bash
python3 -m wikillm ask "What did I save about vector search?" --vault research
```

## Use Telegram

Run the bot:

```bash
python3 -m wikillm serve telegram-bot
```

Available bot commands:

```text
/capture <url-or-text>
/ask <question>
/find <query>
/review
/reviewed <slug>
/stats
/help
```

You can also paste a bare URL. The bot treats it as `/capture`.

Private deployment should set `[telegram].owner_ids` to the allowed Telegram user IDs. If `owner_ids` is empty, the bot is open to anyone who can reach it.

## Rebuild Generated Vault Files

After processing sources, update human-facing indexes:

```bash
python3 -m wikillm build-index
python3 -m wikillm build-todos
```

For all vaults:

```bash
python3 -m wikillm build-index --all
python3 -m wikillm build-todos --all
```

## Troubleshooting

### `no relevant notes found`

The Milvus index may be empty. Run:

```bash
python3 -m wikillm backfill
```

For all vaults:

```bash
python3 -m wikillm backfill --all
```

### `no input adapter handles kind='file'`

The CLI can detect non-PDF local files as `file`, but no `file` adapter is registered. Use:

```bash
python3 -m wikillm distill ./path/to/file.txt --kind text
```

or place `.txt`/`.md` files under `sources/` and run `scan`.

### Telegram captures work but queue processing is slow

The bot drains one inbox item between long-poll cycles. With the default 30 second poll timeout, this is intentionally low throughput and keeps Milvus writes single-owner.

### Feed scans enqueue nothing

Check `data/feed_seen.db`. The entries may already be marked seen. Also confirm the feed entry has a link and that `kind` matches a registered input adapter.
