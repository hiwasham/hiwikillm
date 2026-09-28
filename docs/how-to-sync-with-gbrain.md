# How to Sync wikillm Notes With GBrain

This guide shows how to 
- import `wikillm`'s generated notes 
- into a GBrain source 
- so agents can search and query them through GBrain.

## Prerequisites
- `gbrain` is installed and initialized.
- `config.toml` exists in this repo.
	- If it does not, copy `config.example.toml` to `config.toml` and set `[gateway].openclaw_config`.
- `wikillm` has generated at least one note under `notes/`.
- You are running commands from the project root:

```bash
cd /mnt/d/Obsidi1/03.Projects/hiwikillm
```

Check the tools:

```bash
gbrain --version
python3 -m wikillm vaults
```
خطا [[2026-09-28]]
## Steps

1. If this is a fresh checkout, create local config and runtime folders.

   ```bash
   cp config.example.toml config.toml
   mkdir -p notes sources data todos
   ```

   Edit `config.toml` so `[gateway].openclaw_config` points at your local OpenClaw config, for example `/root/.openclaw/openclaw.json`.

2. Rebuild the note files that are useful to humans and agents.

   ```bash
   python3 -m wikillm build-index --all
   python3 -m wikillm build-todos --all
   ```

   `build-index --all` writes one `index.md` per known note vault. `build-todos --all` writes open-question indexes under `todos/`.

3. Register `wikillm` notes as a GBrain source.

   ```bash
   gbrain sources add hiwikillm-notes --path /root/projects/hiwikillm/notes
   ```

   If the source already exists, list sources and keep the existing entry:

   ```bash
   gbrain sources list
   ```

4. Import the Markdown notes into that source.

   ```bash
   gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
   ```

   Use `gbrain import` here, not `gbrain sync`. `gbrain sync --source ...` requires the source path to be a git repository; `wikillm/notes` is intentionally gitignored runtime content.

5. Query the imported notes through GBrain.

   ```bash
   gbrain query "what do my wikillm notes say about vector search?"
   ```

6. Repeat the import after new captures.

   ```bash
   python3 -m wikillm process --once
   python3 -m wikillm build-index --all
   gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
   ```

## Sync A Single Named Vault

If you want GBrain to index a named vault separately, register that vault folder:

```bash
gbrain sources add hiwikillm-research --path /root/projects/hiwikillm/notes/research
gbrain import /root/projects/hiwikillm/notes/research --source-id hiwikillm-research --workers 4 --json
```

This keeps GBrain source names aligned with `wikillm` vault names.

## Use gstack `/sync-gbrain` For Code Search

`/sync-gbrain` is a gstack workflow for indexing this repository's code and gstack memory into GBrain. It is separate from syncing `wikillm`'s personal notes.

Use both when you want both surfaces:

```text
/sync-gbrain --full
gbrain sources add hiwikillm-notes --path /root/projects/hiwikillm/notes
gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
```

The first command teaches GBrain about the codebase. The import command teaches GBrain about the generated personal wiki notes.

## Verification

Run:

```bash
gbrain sources list
gbrain query "wikillm"
```

You should see `hiwikillm-notes` in the source list, and query results should include pages imported from `notes/`.

Cross-check from `wikillm`:

```bash
python3 -m wikillm ask "what is in my notes?" --mode pointer
```

If `wikillm` can retrieve notes but GBrain cannot, the issue is in GBrain source registration or import. If neither can retrieve notes, process sources or run the `wikillm` backfill commands.

## Troubleshooting

### `gbrain: command not found`

Install and initialize GBrain before following this guide. In a gstack setup, use:

```text
/setup-gbrain
```

Outside gstack, follow the GBrain install instructions for your environment.

### `hiwikillm-notes` Already Exists

List sources:

```bash
gbrain sources list
```

If the existing path is correct, run:

```bash
gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
```

If the path is wrong, remove and re-add it with GBrain's source commands.

### GBrain Finds Old Notes

Rebuild and sync after new captures:

```bash
python3 -m wikillm build-index --all
gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
```

### `Not a git repository: /root/projects/hiwikillm/notes`

You used `gbrain sync --source hiwikillm-notes`. Use import instead:

```bash
gbrain import /root/projects/hiwikillm/notes --source-id hiwikillm-notes --workers 4 --json
```

### Milvus Lock Errors During Capture

GBrain reads Markdown files from `notes/`; it should not open `data/milvus.db`. Keep Milvus single-writer by running only one `wikillm process`, `wikillm distill`, or `wikillm serve telegram-bot` process at a time.

## Related

- [How to Use wikillm With Obsidian](how-to-use-with-obsidian.md)
- [Deep Research: wikillm Integrations](research-wikillm-integrations.md)
- [Architecture Explanation](explanation-architecture.md)
- [CLI Reference](reference-cli.md)
