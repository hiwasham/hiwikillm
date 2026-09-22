# How to Use wikillm With Obsidian

This guide shows how to open `wikillm`'s generated Markdown notes in Obsidian and keep the vault usable without changing `wikillm`'s runtime state.

## Prerequisites

- `wikillm` is configured with a local `config.toml`.
- Obsidian is installed on the machine where you want to browse the notes.
- At least one note has been generated:

```bash
python3 -m wikillm distill https://example.com/
```

If you already have notes, you can skip the example capture.

## Steps

1. Rebuild the generated navigation files.

   ```bash
   python3 -m wikillm build-index
   python3 -m wikillm build-todos
   ```

   `build-index` writes `notes/index.md`. `build-todos` writes `todos/index.md`, which is outside the note vault by default.

2. Open the notes directory as an Obsidian vault.

   Use Obsidian's "Open folder as vault" flow and select:

   ```text
   /root/projects/hiwikillm/notes
   ```

   If this repo is cloned somewhere else, select that clone's `notes/` directory.

3. Start from the generated index.

   Open:

   ```text
   index.md
   ```

   The index groups notes by tag, lists all notes, and shows top `[[entities]]`.

4. Use Obsidian's graph and backlinks.

   Generated notes contain `[[wikilinks]]` in the `## Entities & links` section. Obsidian can use those links for backlinks and graph navigation.

5. Use named vaults when you want separate Obsidian workspaces.

   Capture into a named vault:

   ```bash
   python3 -m wikillm distill https://example.com/ --vault research
   python3 -m wikillm build-index --vault research
   ```

   Then open this folder in Obsidian:

   ```text
   /root/projects/hiwikillm/notes/research
   ```

## Open A Note With An Obsidian URI

`wikillm` does not currently ship an `open-note` command. You can still generate an Obsidian URI for a note path:

```bash
NOTE=$(find notes -name '*.md' ! -name 'index.md' ! -name 'log.md' | sort | tail -1)
python3 -c 'from pathlib import Path; import sys, urllib.parse; print("obsidian://open?path=" + urllib.parse.quote(str(Path(sys.argv[1]).resolve())))' "$NOTE"
```

On a desktop with Obsidian registered as a URI handler, open the printed URI.

## Verification

Run:

```bash
python3 -m wikillm vaults
python3 -m wikillm entities --limit 20
```

Then check Obsidian:

- `index.md` is visible in the file tree.
- Generated notes show frontmatter as Obsidian properties.
- `[[entity]]` links are clickable.
- Graph view shows connections after notes with links exist.

## Troubleshooting

### `notes/` Is Empty

Capture or process at least one source:

```bash
python3 -m wikillm distill https://example.com/
```

Or drain queued captures:

```bash
python3 -m wikillm process --once
```

### A Named Vault Does Not Appear

Named vaults are discovered from direct children of `notes/`. Generate one note in the vault first:

```bash
python3 -m wikillm distill "short note text" --kind text --vault research
python3 -m wikillm vaults
```

### Todos Are Not Visible In Obsidian

`build-todos` writes to `todos/index.md`, not `notes/index.md`. Open `todos/index.md` from the project root, or treat it as a separate task file outside the Obsidian vault.

### Do Not Edit Runtime State From Obsidian

It is fine to edit generated Markdown notes, but do not edit files in `data/`. `data/inbox.db`, `data/milvus.db`, and `data/entities.db` are runtime indexes owned by `wikillm`.

## Related

- [How to Capture Sources and Query Notes](how-to-capture-and-query.md)
- [CLI Reference](reference-cli.md)
- [Configuration Reference](reference-configuration.md)
- [Deep Research: wikillm Integrations](research-wikillm-integrations.md)
