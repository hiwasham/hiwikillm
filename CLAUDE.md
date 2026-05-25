# CLAUDE.md — wikillm

See **[AGENTS.md](AGENTS.md)** for the full operating instructions, layout, plugin protocol, conventions, and common operations. The substantive content is there to keep one source of truth across agent types.

## Claude-Code-specific notes

- This workspace lives under OpenClaw at `~/.openclaw/workspace/wikillm/`. The OpenClaw agent system expects a `.claude/mcp.json` here for MCP server configuration; currently it's empty (Phase A) and ready for Drive/Fetch/GitHub MCPs in Phase E.
- The Telegram bot (`@hiwikillmbot`) and pipeline are *separate* from the OpenClaw Telegram bot — see [[reference-openclaw]] memory. Don't confuse the two.
- When asked to "ship a Phase B/C/D item", use `TaskCreate` to plan, then ship the layered plugin (don't modify core/ if you can avoid it).
- For end-to-end verification of any change touching distillation, run `python3 -m wikillm distill https://example.com/` and inspect the produced note — that exercises the full input → knowledge stack.
