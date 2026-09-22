# Deep Research: GBrain, Obsidian, wikillm, and Research Tooling

Generated: 2026-07-08

Scope: a practical architecture for managing a long-lived Obsidian vault of about 20,000 notes, the local GBrain installation, and `wikillm` as a source distillation and cited Q&A pipeline. This also compares web/deep-research tools such as Firecrawl, Tavily, Exa, and Jina Reader.

## Executive Summary

The best architecture is layered, not merged:

- **Obsidian** remains the human source of truth and editing environment for the 20,000-note vault.
- **GBrain** becomes the large-scale index, graph, agent memory, MCP surface, and cross-project reasoning layer over Obsidian and `wikillm`.
- **wikillm** remains the capture/distillation pipeline for new resources: URLs, YouTube, GitHub repos, PDFs, text drops, feeds, and selected Obsidian/GBrain exports.
- **Firecrawl** should be added as an optional high-fidelity web fetcher and crawler, not as the primary memory system.

Do not start by importing and rewriting the whole Obsidian vault through `wikillm`. That creates sync-loop and trust problems. Start read-only: register the existing Obsidian vault as a GBrain source, register `wikillm/notes` as a separate GBrain source, then use `wikillm` for new source capture and curated note generation.

## Current Local Findings

Local GBrain version:

```bash
gbrain 0.42.25.0
```

Useful installed GBrain surfaces observed locally:

- `gbrain sources add/list`
- `gbrain sync --source <id>`
- `gbrain sync --all --workers N --parallel N`
- `gbrain query`
- `gbrain ask`
- `gbrain import`
- MCP serving commands via the installed CLI

`gbrain sync --help` shows that sync supports incremental operation, source scoping, `--full`, `--dry-run`, `--watch`, `--no-embed`, `--no-extract`, `--workers`, `--all`, `--parallel`, `--json`, and `--yes`. Local source inspection also shows that `gbrain sync` requires a git repository. For non-git Markdown folders, including `wikillm/notes` and many Obsidian vaults, use `gbrain import <dir> --source-id <id>` instead.

One operational warning from the previous local `gbrain doctor --fast --json`: `~/.gbrain` appears to live inside the `/root` git worktree. That is an accidental-commit risk. The safer future setup is to set `GBRAIN_HOME` to a non-repo location before initializing or migrating GBrain state.

## Source-Backed Findings

### Obsidian

Obsidian stores note properties as YAML frontmatter and treats `tags`, `aliases`, and `cssclasses` as default properties. It supports internal links using wikilinks and Markdown links, including links to headings and blocks. Obsidian URI supports automation actions such as opening, creating, searching, and appending notes.

Sources:

- Obsidian Properties: https://help.obsidian.md/properties
- Obsidian Internal Links: https://help.obsidian.md/links
- Obsidian URI: https://help.obsidian.md/Extending+Obsidian/Obsidian+URI

Implication: `wikillm` should keep writing portable Markdown with YAML properties and `[[wikilinks]]`. It should avoid Obsidian-only block references in generated notes unless the user explicitly opts in.

### GBrain

GBrain presents itself as a persistent brain layer for agents and local knowledge, with Markdown import/sync, query/ask commands, graph-oriented behavior, and MCP exposure. The local CLI confirms multi-source sync and incremental operation.

Sources:

- GBrain GitHub repository: https://github.com/garrytan/gbrain
- Local CLI: `gbrain --version`, `gbrain sync --help`, `gbrain sources list`
- Local docs previously reviewed: `/root/gbrain/README.md`, `/root/gbrain/docs/GBRAIN_RECOMMENDED_SCHEMA.md`, `/root/gbrain/docs/guides/agent-to-gbrain.md`

Implication: GBrain should index the full Obsidian vault and `wikillm` notes directly. `wikillm` should not reimplement GBrain's graph, MCP, or large-vault indexing layer.

### wikillm

`wikillm` already writes Markdown notes under `notes/`, uses YAML frontmatter, preserves `[[wikilinks]]`, indexes chunks into Milvus Lite, extracts entity links into SQLite, and generates `index.md` plus `todos/`.

Local surfaces:

- `python3 -m wikillm distill <ref>`
- `python3 -m wikillm process --once`
- `python3 -m wikillm ask <question>`
- `python3 -m wikillm find <query>`
- `python3 -m wikillm build-index --all`
- `python3 -m wikillm build-todos --all`
- `python3 -m wikillm backfill`

Implication: `wikillm` is best used for new resource capture and distilled research notes. For your existing 20,000 Obsidian notes, it should consume selected note sets or query GBrain, not own the whole vault.

### Firecrawl

Firecrawl is a strong fit for web capture. Its public documentation describes API surfaces for scraping, crawling, mapping, searching, and extracting web content. A Firecrawl API key should be stored locally, not pasted into chat.

Sources:

- Firecrawl docs: https://docs.firecrawl.dev/
- Firecrawl API reference: https://docs.firecrawl.dev/api-reference/introduction

Implication: add Firecrawl as an optional `wikillm` URL fetch backend:

```toml
[fetch]
backend = "firecrawl"
firecrawl_api_key_env = "FIRECRAWL_API_KEY"
```

Firecrawl should improve source acquisition, especially for JavaScript-heavy pages, docs sites, and multi-page research. It should not replace GBrain or Obsidian.

### Tavily

Tavily is built around search and extract APIs for AI agents and also offers research-oriented endpoints in its docs. It is useful when the task is "find relevant web sources and summarize evidence" rather than "crawl this known site."

Source:

- Tavily docs: https://docs.tavily.com/

Implication: Tavily is a candidate for a `research-search` adapter, especially for broad discovery. It is less central than Firecrawl for `wikillm`'s current URL ingestion path.

### Exa

Exa is a neural search API with search and content-retrieval endpoints. It is strongest when you need semantically relevant source discovery beyond keyword search.

Source:

- Exa docs: https://docs.exa.ai/

Implication: Exa is a good source-discovery layer for "find the best papers/posts/repos about X", then Firecrawl or existing adapters can fetch the selected sources.

### Jina Reader

Jina Reader exposes URL-to-reader style conversion and is often useful for turning a web page or PDF URL into LLM-friendly text/Markdown with low integration overhead.

Source:

- Jina Reader: https://jina.ai/reader/

Implication: Jina Reader is a good fallback fetcher for simple capture and quick experiments. Firecrawl is the better paid/high-fidelity crawler when you already have an API key.

## Recommended Architecture

```text
                    +----------------------+
                    |      Obsidian        |
                    |  20k-note vault UI   |
                    +----------+-----------+
                               |
                         read-only sync
                               |
+----------------+     +-------v--------+      +----------------+
| Firecrawl/Exa/ |     |     GBrain     |      |    Agents      |
| Tavily/Jina    +-----> sources + graph +<----> MCP/query/ask   |
+-------+--------+     +-------+--------+      +----------------+
        |                      ^
        | fetched sources      |
        v                      | sync notes/
+-------+--------+             |
|    wikillm     +-------------+
| distill/index  |
+-------+--------+
        |
        v
   notes/YYYY/MM/*.md
```

Layer responsibilities:

- Obsidian: canonical personal notes, manual editing, backlinks, graph, daily work.
- GBrain: indexing, graph traversal, agent memory, MCP, large-vault search, cross-source synthesis.
- wikillm: new source ingestion, distillation, cited Q&A over captured notes, generated indexes/todos.
- Firecrawl/Exa/Tavily/Jina: external web acquisition and discovery.

## Practical Setup Plan

### 1. Put Secrets In A Local Ignored File

`.secrets/` is now gitignored. Store API keys there:

```bash
mkdir -p .secrets
printf 'FIRECRAWL_API_KEY=fc-YOUR_KEY_HERE\n' > .secrets/research.env
chmod 600 .secrets/research.env
```

Then a command can load it locally:

```bash
set -a
source .secrets/research.env
set +a
```

Do not paste API keys into chat or commit them.

### 2. Register The Obsidian Vault In GBrain

Use a stable source name. Example:

```bash
gbrain sources add obsidian-main --path "/path/to/your/obsidian/vault"
gbrain import "/path/to/your/obsidian/vault" --source-id obsidian-main --workers 4 --json
```

For the first pass, keep this read-only from the agent side. Do not let automation rewrite 20,000 notes. If your Obsidian vault is a git repository and you want incremental git-aware sync, `gbrain sync --source obsidian-main --workers 4 --json` is also valid.

If your Obsidian vault has many bare `[[note-name]]` links across folders, evaluate GBrain's basename link resolution before enabling it globally:

```bash
gbrain config get link_resolution.global_basename
```

If available and appropriate:

```bash
gbrain config set link_resolution.global_basename true
```

Only enable this if collision behavior is acceptable for your vault.

### 3. Register wikillm Notes Separately

```bash
cd /root/projects/hiwikillm
cp config.example.toml config.toml
mkdir -p notes sources data todos
python3 -m wikillm build-index --all
python3 -m wikillm build-todos --all
gbrain sources add hiwikillm-notes --path /root/projects/hiwikillm/notes
gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
```

Edit `config.toml` before running `wikillm` commands. Keep `obsidian-main` and `hiwikillm-notes` separate. That makes source attribution and debugging easier.

### 4. Add Firecrawl As An Optional wikillm Fetch Backend

First implementation target:

- Keep the existing stdlib/httpx URL adapter as default.
- Add `fetch.backend = "firecrawl"` as an opt-in.
- Use `FIRECRAWL_API_KEY` from the environment.
- Return Markdown/text to the existing `llm-distill` stage.

This improves capture without changing the knowledge pipeline.

### 5. Add A Research Command Later

After Firecrawl works as a fetcher, add a separate research flow:

```bash
python3 -m wikillm research "best tools for long-term personal knowledge graphs" --vault research
```

Likely behavior:

1. Discover sources with Exa or Tavily.
2. Fetch chosen pages with Firecrawl.
3. Distill each source into `wikillm` notes.
4. Generate one synthesis note with citations.
5. Sync `hiwikillm-notes` into GBrain.

## Tool Decision Matrix

| Tool | Best Use | Avoid Using It For |
|---|---|---|
| Obsidian | Human authoring, browsing, backlinks, graph, daily knowledge work | Background indexing, agent memory, automated large-scale rewriting |
| GBrain | Large-vault indexing, agent memory, graph/query/MCP over many sources | Replacing Obsidian as the human editor |
| wikillm | Distilling new resources into structured notes, cited Q&A over captured notes | Owning or rewriting the whole existing Obsidian vault |
| Firecrawl | Fetching/crawling known websites and docs into clean text/Markdown | Acting as long-term memory |
| Exa | Semantic web/source discovery | Crawling whole sites |
| Tavily | Agentic web search and research-style source gathering | Local vault indexing |
| Jina Reader | Fast URL/PDF-to-Markdown fallback | Complex site crawling or authenticated workflows |
| Readwise Reader | Reading queue/highlight source | Canonical vault or graph layer |
| Zotero | Papers, metadata, PDFs, citations | General personal wiki |

## Risks

- **Sync loops:** Do not have Obsidian, GBrain, and `wikillm` all rewrite each other's files.
- **Large-vault collisions:** 20,000 notes probably contain duplicate titles and ambiguous wikilinks. Any basename link resolution needs collision reporting.
- **Milvus Lite locking:** `wikillm`'s Milvus Lite database is single-writer. Avoid multiple simultaneous `wikillm process`, `distill`, or Telegram bot indexing processes.
- **Secret leakage:** Firecrawl and other API keys must stay in ignored files or environment variables.
- **Over-automation:** A decade-old Obsidian vault has personal conventions. Start with read-only indexing and dashboards before automatic cleanup.

## Best Next Build Steps

1. Add a `firecrawl` fetch backend to `wikillm/inputs/url.py` or a new `wikillm/inputs/firecrawl_url.py`.
2. Add `docs/how-to-use-firecrawl.md` with the `.secrets/research.env` setup.
3. Add `python3 -m wikillm sync-gbrain` as a thin wrapper around `gbrain sources add` and `gbrain sync`.
4. Run a read-only GBrain sync of your Obsidian vault and inspect collisions/orphans.
5. Add a dashboard note: "new wikillm captures connected to old Obsidian notes."

## Office-Hours Question

For this to become genuinely useful with your 20,000-note vault, the first product-quality workflow should be one of these:

- Find old notes that are relevant to a new capture.
- Deduplicate and cluster old notes.
- Connect new web/PDF/GitHub resources to old Obsidian notes.
- Give agents durable memory over the whole vault.
- Create daily or weekly review queues.

My recommendation is to start with **connect new resources to old notes**. It uses all three layers cleanly: `wikillm` captures and distills, GBrain finds old related material, and Obsidian remains where you review and edit.
