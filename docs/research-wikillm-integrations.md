# Deep Research: wikillm Integrations

Generated: 2026-07-07

Scope: integration strategy for `wikillm`, especially Obsidian, GBrain/gstack, MCP, and adjacent knowledge tools such as Readwise, Zotero, and Logseq.

## Executive Summary

`wikillm` is already well-shaped for Obsidian because it writes ordinary Markdown files with YAML frontmatter, `[[wikilinks]]`, tags, and stable sections. Obsidian's official docs confirm that properties are stored as YAML at the top of Markdown files, links support `[[wikilink]]` syntax, and URI automation can open, create, append, or prepend notes. The best near-term Obsidian integration is therefore not a plugin. It is a stricter vault contract: make `notes/` a first-class Obsidian vault or subfolder, add Obsidian-friendly properties, and generate index/todo/entity pages that Obsidian can navigate.

GBrain is the strongest complementary system, not a replacement. `wikillm` is source distillation and personal note generation. GBrain is agent memory, hybrid retrieval, graph traversal, MCP, and code/source indexing. The right integration is two-way but asymmetric: import `wikillm` notes into GBrain as a source, and optionally let `wikillm` capture GBrain reports or pages as inputs. Avoid duplicating GBrain's graph and MCP layer inside `wikillm`.

The highest-leverage Phase F is an integration hardening phase:

1. Obsidian vault contract and URI helpers.
2. GBrain source registration/sync docs and optional command wrapper.
3. Readwise Reader import/export path.
4. Zotero local API scanner for papers and annotations.
5. MCP server for `wikillm` query/capture operations.

## Current wikillm Integration Surface

From the repo:

- Notes are written to `notes/YYYY/MM/<slug>.md` for the default vault and `notes/<vault>/YYYY/MM/<slug>.md` for named vaults.
- Note frontmatter currently includes `title`, `source`, `kind`, `captured_at`, `page_type`, and `tags`.
- Required sections are `## TL;DR`, `## Key claims & findings`, `## Entities & links`, `## Open questions`, and `## Source`.
- `entity-index` extracts `[[wikilinks]]` into `data/entities.db`.
- `build-index` writes `notes/index.md` with notes by tag, all notes, and top entities.
- `build-todos` writes `todos/index.md` from note open questions.
- `scan` ingests `.pdf`, `.txt`, `.md`, and `.url` files from `sources/`.
- `scan-feeds` ingests RSS/Atom entries from `config.toml`.
- Milvus Lite backs semantic query; SQLite backs inbox, entities, feeds, and review state.

This means `wikillm` already has a good "plain files plus local indexes" architecture. The main gap is integration contracts and sync boundaries, not core capability.

## Source-Backed Findings

### Obsidian

Obsidian stores properties as YAML at the top of the file. It supports text, list, number, checkbox, date, date-time, and tag property types. It treats `tags`, `aliases`, and `cssclasses` as default properties. Source: Obsidian Help, Properties: https://obsidian.md/help/properties

Obsidian supports internal links in both wikilink format and Markdown link format. Wikilinks are the default; Obsidian recommends Markdown links when interoperability is important. Source: Obsidian Help, Internal links: https://obsidian.md/help/links

Obsidian links can point to files, headings, and blocks. Block references are Obsidian-specific and not standard Markdown. Source: Obsidian Help, Internal links: https://obsidian.md/help/links

Obsidian URI supports automation actions including `open`, `new`, `daily`, `unique`, and `search`. The `open` action can open by vault and file or absolute path. The `new` action can create a note with content, append to an existing note, overwrite, or run silently. Source: Obsidian Help, Obsidian URI: https://obsidian.md/help/Extending%2BObsidian/Obsidian%2BURI

Implication for `wikillm`: write normal Markdown and avoid Obsidian-only block refs in generated notes. Add optional `obsidian://open?path=...` links in CLI/bot output for local desktop use, but keep note content portable.

### GBrain And GStack

GBrain positions itself as a persistent brain for AI agents, with synthesis, graph traversal, gap analysis, and MCP surfaces. Its README describes local PGLite setup, Markdown import, query, and MCP serving. Source: GBrain README: https://github.com/garrytan/gbrain

The local installed CLI exposes `gbrain import <dir>`, `gbrain sync --repo <path>`, `gbrain sources add <id> --path <p>`, `gbrain sync --source <id>`, `gbrain query`, `gbrain ask`, `gbrain embed`, graph commands, code-index commands, and MCP serving through `gbrain serve` and `gbrain serve --http`. Source: local `gbrain --help`, observed 2026-07-07. Later verification on 2026-07-08 showed that `gbrain sync --source <id>` requires a git repository, so gitignored Markdown folders such as `wikillm/notes` should use `gbrain import <dir> --source-id <id>`.

GStack's GBrain guide says `/sync-gbrain` registers the current working tree as a federated source, writes a `.gbrain-source` pin file, runs `gbrain sync --strategy code`, and can add guidance to `CLAUDE.md` after a capability check. Source: `/root/.gstack/repos/gstack/USING_GBRAIN_WITH_GSTACK.md`

GStack's brain sync docs say gstack state can be pushed to a private git repo and wired into local GBrain as a federated source via `gbrain sources add` and sync. Source: `/root/.gstack/repos/gstack/docs/gbrain-sync.md`

Implication for `wikillm`: do not rebuild GBrain. Register `notes/` or the repo as a GBrain source and sync it. Consider adding `.gbrain-source` support and a small wrapper command only if it removes manual steps.

### MCP

MCP is an open-source standard for connecting AI applications to external systems such as files, databases, tools, and workflows. Source: Model Context Protocol docs: https://modelcontextprotocol.io/docs/getting-started/intro

The official MCP servers repository includes reference servers such as filesystem, git, fetch, memory, and time, and notes that reference servers demonstrate features rather than provide production-ready solutions. Source: MCP servers README: https://github.com/modelcontextprotocol/servers

The reference filesystem server provides secure file operations with configurable access controls, and the git server provides tools to read, search, and manipulate repositories. Source: MCP servers README: https://github.com/modelcontextprotocol/servers

Implication for `wikillm`: a `wikillm` MCP server should expose high-level operations, not raw filesystem access:

- `capture(ref, kind?, vault?)`
- `ask(question, mode?, vault?, top_k?)`
- `find(query, vault?, top_k?)`
- `list_vaults()`
- `entities(vault?, limit?)`
- `due_reviews(limit?)`

Raw note file access can be delegated to filesystem MCP when needed.

### Readwise And Reader

Readwise's official Obsidian plugin can automatically sync highlights into Obsidian. It creates a new page for new documents and appends new highlights to existing pages. It is append-only and does not overwrite user edits. Source: Readwise Obsidian export docs: https://docs.readwise.io/readwise/docs/exporting-highlights/obsidian

Readwise's Obsidian export supports customization of properties/YAML frontmatter, page title, metadata, highlight formatting, sync notifications, file/folder names, and full document export. Source: Readwise Obsidian export docs: https://docs.readwise.io/readwise/docs/exporting-highlights/obsidian

Reader API supports saving new documents and fetching documents. Auth uses an `Authorization: Token XXX` header. Document create uses `POST https://readwise.io/api/v3/save/` and accepts URL, HTML, title, author, summary, published date, image URL, location, category, tags, and notes. Source: Reader API: https://readwise.io/reader_api

Implication for `wikillm`: Readwise should be treated as both an upstream source and optional downstream sink. For upstream, add a Reader scanner that fetches documents/highlights and enqueues them as `url` or `text`. For downstream, `wikillm` probably should not push every distilled note into Reader unless the user explicitly wants Reader as a reading queue.

### Zotero

Zotero Web API v3 provides read-only access to online Zotero libraries, and the Zotero desktop client exposes the same endpoints locally at `http://localhost:23119/api/`. Source: Zotero Web API basics: https://www.zotero.org/support/dev/web_api/v3/basics

Zotero API resources include collections, items, child items, tags, saved searches, and groups. Source: Zotero Web API basics: https://www.zotero.org/support/dev/web_api/v3/basics

Zotero supports incremental sync patterns with `Last-Modified-Version`, conditional requests, and `?since=`. Source: Zotero Web API basics: https://www.zotero.org/support/dev/web_api/v3/basics

Zotero item export formats include BibTeX, BibLaTeX, CSL JSON, CSV, RIS, RDF variants, and more. Source: Zotero Web API basics: https://www.zotero.org/support/dev/web_api/v3/basics

Better BibTeX offers automatic export from Zotero. Source: Better BibTeX automatic export docs: https://retorque.re/zotero-better-bibtex/exporting/auto/

Implication for `wikillm`: the best Zotero integration is a local scanner using `localhost:23119/api/` when Zotero is running. Store a local `data/zotero_seen.db` keyed by item key and version. Enqueue PDFs through the existing `pdf` adapter and item metadata/notes through `text`.

### Logseq

Logseq's GitHub README describes it as a privacy-first, open-source knowledge platform with support for Markdown and Org-mode. Source: Logseq GitHub README: https://github.com/logseq/logseq

Logseq can create a graph from an existing directory containing Markdown files; community docs say it creates folders such as `journals`, `pages`, and `assets`, and can find files in subfolders. Source: Logseq docs/community page surfaced from docs.logseq.com: https://docs.logseq.com/

Implication for `wikillm`: Logseq compatibility should be a secondary target. `wikillm`'s Markdown notes can be opened by Logseq, but Logseq's block-oriented model and folder conventions are not the best primary fit. Obsidian is the better first-class Markdown vault target.

## Integration Recommendations

### 1. Make Obsidian The First-Class Human UI

Status: high-confidence, low-risk.

Recommended changes:

- Add `docs/how-to-use-with-obsidian.md`.
- Add config keys:

```toml
[obsidian]
vault_name = "wikillm"
open_links = true
```

- Add CLI helper:

```bash
python3 -m wikillm open-note <slug-or-path>
```

This would print or launch an `obsidian://open?path=...` URI.

- Add optional properties to generated notes:

```yaml
wikillm_id: "<stable hash>"
vault: "default"
status: "captured"
review_count: 0
```

Use scalar/list/date fields only. Do not put Markdown in properties.

Rationale:

- Obsidian already understands YAML properties and wikilinks.
- `wikillm` already writes Markdown.
- URI automation can improve CLI and Telegram output without an Obsidian plugin.

Avoid:

- Obsidian block refs in generated notes.
- Relying on Dataview as a required dependency.
- A custom Obsidian plugin before the file contract is hardened.

### 2. Add A GBrain Sync Recipe

Status: high-confidence, medium-risk because it touches another local knowledge system.

Recommended first version:

```bash
gbrain sources add hiwikillm-notes --path /root/projects/hiwikillm/notes
gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
```

Then document:

```bash
gbrain query "what do my wikillm notes say about ..."
```

Possible `wikillm` wrapper:

```bash
python3 -m wikillm sync-gbrain
```

Minimum behavior:

- Detect `gbrain` on PATH.
- Register `notes/` as a source if missing.
- Run `gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes`.
- Print next commands.

Do not write into `~/.gbrain` directly. Use the `gbrain` CLI.

### 3. Build A Readwise/Reader Scanner

Status: high-value if the user reads heavily in Reader.

Recommended scanner:

```bash
python3 -m wikillm scan-reader
```

Config:

```toml
[reader]
token_env_var = "READWISE_TOKEN"
location = "archive"
vault = "reading"
```

State:

```text
data/reader_seen.db
```

Implementation path:

- Use Reader API auth header.
- Fetch documents incrementally if the API endpoint supports it.
- Enqueue document URL as `url` when public content is enough.
- Enqueue API-returned title/summary/notes/highlights as `text` when the API provides richer data.

Design lesson from Readwise Obsidian plugin: prefer append-only or new-note behavior. Never rewrite user-edited notes without an explicit command.

### 4. Build A Zotero Local Scanner

Status: strong fit for papers/PDFs.

Recommended scanner:

```bash
python3 -m wikillm scan-zotero
```

Config:

```toml
[zotero]
base_url = "http://localhost:23119/api"
library = "users/local"
vault = "research"
```

State:

```text
data/zotero_seen.db
```

Implementation path:

- Use local API first because it requires no auth and reads local desktop data.
- Use item keys and library versions for incremental sync.
- Enqueue child PDFs as `pdf`.
- Enqueue item metadata, abstracts, notes, collections, tags, DOI, and citation data as `text`.
- Preserve Zotero item key in note frontmatter as `zotero_key`.

### 5. Add A wikillm MCP Server

Status: strategic, should come after Obsidian/GBrain contracts.

The MCP server should not expose raw DB writes. It should expose the product verbs:

- capture
- ask
- find
- list vaults
- list entities
- due reviews
- mark reviewed

This lets Claude Code, Codex, OpenClaw, and other MCP clients use `wikillm` without shell command parsing.

Potential transport:

- stdio first for local agents.
- HTTP later if remote capture/query is needed.

Security:

- Read-only tools by default.
- Capture and reviewed mutate state, so they should be explicit tools.
- No access to `config.toml`, tokens, or raw DB paths.

## Proposed Phase F

### F1: Obsidian Contract

Deliverables:

- `docs/how-to-use-with-obsidian.md`
- `obsidian://` open helper
- optional `[obsidian]` config section
- note frontmatter additions with backward-compatible parser behavior

Acceptance:

- A generated note opens cleanly in Obsidian.
- Properties render as Obsidian properties.
- Links show in graph view.
- README explains how to point Obsidian at `notes/`.

### F2: GBrain Sync

Deliverables:

- `docs/how-to-sync-with-gbrain.md`
- optional `wikillm sync-gbrain` wrapper
- `.gbrain-source` guidance if using gstack `/sync-gbrain`

Acceptance:

- `gbrain sources list` shows `hiwikillm-notes`.
- `gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes` succeeds.
- `gbrain query` can retrieve a known `wikillm` note.

### F3: Reader And Zotero Sources

Deliverables:

- `scan-reader`
- `scan-zotero`
- `data/reader_seen.db`
- `data/zotero_seen.db`
- docs for token/local API setup

Acceptance:

- New Reader document enqueues once.
- New Zotero PDF enqueues once.
- Re-running scanners is idempotent.

### F4: MCP Surface

Deliverables:

- `wikillm serve mcp` or separate `wikillm_mcp` module
- MCP tools for query and capture
- docs for Claude/Codex/OpenClaw registration

Acceptance:

- MCP client can ask a question over notes.
- MCP client can capture a URL.
- No secret/config contents exposed.

## Risks And Design Constraints

### Do Not Make Obsidian The Source Of Truth For Runtime State

Obsidian should own human editing. `wikillm` should own ingestion, indexing, and generated artifacts. Keep runtime state in `data/`.

### Do Not Let Multiple Processes Write Milvus

Keep the single-writer rule. If scanners expand, they should enqueue to SQLite. One processor should drain and index.

### Keep Note Schema Backward-Compatible

Frontmatter and section names are parsed by multiple modules. Add fields freely, but rename fields or sections only with a migration.

### Avoid Sync Loops

If Readwise exports to Obsidian and `wikillm` scans the same Obsidian folder, it may ingest generated Readwise pages. This can be useful, but it needs a clear folder allowlist or source marker to avoid recursive captures.

### Separate Human Notes From Machine Reports

GBrain reports, gstack recovery docs, and `wikillm` distilled notes can all be Markdown. Use folders or frontmatter `kind`/`source_kind` fields so tools know what they are reading.

## Ranked Roadmap

| Rank | Work | Why now | Complexity |
| ---: | --- | --- | --- |
| 1 | Obsidian usage doc + URI helper | Matches current Markdown output immediately | Low |
| 2 | GBrain sync doc + wrapper | Gives agents stronger retrieval without new indexing code | Low-medium |
| 3 | Fix smoke test and add plugin tests | Prevents integration regressions | Low |
| 4 | Zotero local scanner | Strong source fit for PDFs/research | Medium |
| 5 | Reader scanner | Strong source fit for web reading/highlights | Medium |
| 6 | MCP server | Strategic agent integration | Medium-high |
| 7 | Obsidian plugin | Only needed after file/URI integration hits limits | High |

## Source Index

- Obsidian Properties: https://obsidian.md/help/properties
- Obsidian Internal Links: https://obsidian.md/help/links
- Obsidian URI: https://obsidian.md/help/Extending%2BObsidian/Obsidian%2BURI
- GBrain README: https://github.com/garrytan/gbrain
- Local GBrain CLI: `gbrain --help`, observed 2026-07-07
- GStack GBrain guide: `/root/.gstack/repos/gstack/USING_GBRAIN_WITH_GSTACK.md`
- GStack brain sync docs: `/root/.gstack/repos/gstack/docs/gbrain-sync.md`
- MCP Introduction: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP reference servers: https://github.com/modelcontextprotocol/servers
- Readwise Obsidian export: https://docs.readwise.io/readwise/docs/exporting-highlights/obsidian
- Reader API: https://readwise.io/reader_api
- Zotero Web API basics: https://www.zotero.org/support/dev/web_api/v3/basics
- Better BibTeX automatic export: https://retorque.re/zotero-better-bibtex/exporting/auto/
- Logseq repository: https://github.com/logseq/logseq
