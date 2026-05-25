# wikillm — Personal Wiki-LLM

Karpathy-style personal knowledge system. Inputs get distilled by an LLM into structured Markdown notes; those notes become both a hand-readable vault and a searchable index.

**Status**: Phase A done. URL → distilled note works end-to-end via CLI.

## Three-layer plugin architecture

Every concrete piece of behavior lives in one of three layers. Each layer is independently extensible: add a new plugin by dropping a file in the right directory and adding one import line.

### 1. Input layer (`wikillm/inputs/`)

Pluggable source adapters. Each fetches raw text for a given reference.

**Contract** (`wikillm/core/types.py::InputAdapter`):
```python
class MyInput:
    name: str                                                 # unique short id
    def matches(self, ref: str, *, kind_hint: str | None) -> bool: ...
    def fetch(self, config: Config, item: RawItem) -> str: ...
```

Today: `url`. Phase B adds: `youtube`, `github`, `pdf`, `text`, `telegram_forward`, `drive_scan`. Future: `notebooklm`, `rss`, `subreddit`, `youtube_channel`, `email_imap`, `kindle_highlights`, `voice_memo`, `screenshots_folder`.

**To add a new input**: write `wikillm/inputs/myinput.py` with a class that implements the contract, end the file with `register_input(MyInput())`, and add `from . import myinput` to `wikillm/inputs/__init__.py`. Done.

### 2. Knowledge layer (`wikillm/knowledge/`)

Pluggable ordered stages that mutate a `PipelineState`. Each stage either transforms (e.g. `llm-distill` produces a `DistilledNote`) or has side effects (e.g. `markdown-vault` writes a file, `milvus-index` upserts embeddings).

**Contract** (`wikillm/core/types.py::KnowledgeStage`):
```python
class MyStage:
    name: str
    def run(self, config: Config, state: PipelineState) -> None: ...
```

Today: `llm-distill`, `markdown-vault`. Phase C adds: `milvus-index`. Phase D adds: `entity-link-extractor`. Future: `graph-store`, `crewai-pipeline`, `airflow-dag`, `dashboard-data`, `spaced-repetition-scheduler`.

Stages run in the order their modules are imported in `wikillm/knowledge/__init__.py`. To insert a stage between two others, reorder the imports there.

### 3. Output layer (`wikillm/outputs/`)

Pluggable consumers of the knowledge layer. Each is something the user interacts with.

**Contract** (`wikillm/core/types.py::OutputAdapter`):
```python
class MyOutput:
    name: str
    def serve(self, config: Config, registry) -> None: ...    # may block (bot/server)
```

Phase C adds: `telegram-qa` (pointer + synthesis modes), `claude-code-session`. Future: `weekly-digest-email`, `video-summary` (diffusion), `podcast-generator` (TTS), `graph-viz`, `dashboard`, `slack-bot`, `discord-bot`, `voice-call-bot`.

## Layout

```
.claude/mcp.json            Phase B: Drive, Fetch, GitHub MCPs
config.toml                 paths, gateway base URL, model aliases, Milvus
data/inbox.db               SQLite capture queue (created on first run)
notes/YYYY/MM/<slug>.md     distilled outputs — sync into Obsidian via Drive
sources/                    raw inputs the user drops in (Phase B: Drive-mirrored)
wikillm/                    Python package
  cli.py                    `python -m wikillm {enqueue|process|stats|distill|list-plugins}`
  pipeline.py               orchestrator — input fetch -> knowledge stages
  core/
    types.py                RawItem, DistilledNote, PipelineState, Protocols
    registry.py             INPUTS / KNOWLEDGE_STAGES / OUTPUTS + load_all()
    config.py               loads config.toml + dotted token lookup
    queue.py                SQLite inbox
    llm.py                  OpenAI-compatible chat client
  inputs/                   one file per source adapter
  knowledge/                one file per stage (ordered)
  outputs/                  one file per output adapter
scripts/smoke_test.sh
```

## Phase A quickstart (verified working)

```bash
cd ~/.openclaw/workspace/wikillm
python3 -m wikillm list-plugins                    # see what's registered
python3 -m wikillm distill https://karpathy.ai/    # one-shot, bypass queue
python3 -m wikillm enqueue https://example.com/    # queue mode
python3 -m wikillm process --once                  # drain one item
python3 -m wikillm stats                           # inbox counts
```

## Configuration

Edit `config.toml`. Auth tokens are NOT duplicated here — the file declares a `token_path`
(a dotted path into `~/.openclaw/openclaw.json`) so swapping providers is a config change.

Default endpoint: `https://api.freemodel.dev/v1` (model: `gpt-5.5`). To use a different provider, point `gateway.base_url` and `gateway.token_path` at it.

## Next phases

See `/home/miraddo/.claude/plans/i-have-obsidian-on-refactored-cook.md` for the full phased roadmap (B, C, D, E) and the future-plugin catalog per layer.
