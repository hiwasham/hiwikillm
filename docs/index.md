# wikillm Documentation

Use this page as the control panel for the project docs and recovery packet.

## Product Docs

| Need | Open |
| --- | --- |
| Start from a clean setup | [Getting Started With wikillm](tutorial-getting-started.md) |
| Capture sources and ask questions | [How to Capture Sources and Query Notes](how-to-capture-and-query.md) |
| Browse generated notes in Obsidian | [How to Use wikillm With Obsidian](how-to-use-with-obsidian.md) |
| Sync notes into GBrain | [How to Sync wikillm Notes With GBrain](how-to-sync-with-gbrain.md) |
| Extend the plugin system | [How to Add a Plugin](how-to-add-a-plugin.md) |
| Look up command behavior | [CLI Reference](reference-cli.md) |
| Look up config and local state | [Configuration Reference](reference-configuration.md) |
| Understand the design | [Architecture Explanation](explanation-architecture.md) |
| Read integration research | [Deep Research: wikillm Integrations](research-wikillm-integrations.md) |

## Recovery Docs

| Need | Open |
| --- | --- |
| Understand what was recovered | [Recovery Report](project-recovery.md) |
| Explain the project to another LLM | [Project Story](project-story.md) |
| Decide what to commit | [Commit Plan](artifacts/COMMIT_PLAN.md) |
| Resume work this week | [Dashboard](artifacts/DASHBOARD.md) |
| Continue the active build packet | [Build Packet](artifacts/BUILD-PACKET.md) |
| Review full recovered conversations | [Transcript HTML](artifacts/project-recovery-transcripts.html) |
| Inspect raw ranking evidence | [Evidence JSON](artifacts/project-recovery-evidence.json) |

## Canonical Location

`/root/projects/hiwikillm`

## Git Status

`minimal`

## Preview

From this project directory:

```bash
mkdocs serve --dev-addr 0.0.0.0:8000
```

Then open:

```text
http://89.167.19.64:8000/
```

Build static HTML:

```bash
mkdocs build
```
