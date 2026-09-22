---
project: "[[Project Name]]"
target_ip: "[[BUILD-PACKET.md]]"
status: "#active"
roa_priority: "High"
last_freeze: "YYYY-MM-DD"
---

# Project Dashboard: [App Name]

> Golden Rule: This file is for meta-work: deciding what to do, preserving project state, and protecting attention.
> Do execution work in `BUILD-PACKET.md`.

## This Week's Focus

Work in one Intermediate Packet at a time: a small, shippable unit that can survive interruption.

- Active Intermediate Packet: [[BUILD-PACKET.md]]
- Done Looks Like: [Describe the tangible stop condition. Example: "A login button that works end to end."]

## Iron Triangle

Time and energy are constraints. Scope is the variable. If capacity drops, downscope instead of quitting.

- Time: [Fixed deadline or review point. Example: Friday 5:00 PM]
- Scope: [Current version. Example: V1 basic functionality, not polished V2.]
- Energy Level: [High / Medium / Low]

## Critical Path

Only list tasks that must happen to ship the current Intermediate Packet. If delaying a task delays the whole packet, it belongs here.

1. [ ] [Main dependency]
2. [ ] [Current bottleneck]
3. [ ] [Final QA or ship check]

## Project Parking Lot

Capture distractions, V2 ideas, and unrelated research here. Do not act on them during the current packet.

- [ ] [Future idea, question, or research topic]

## Last Session Freeze

This is a bookmark for your future self. Update it before stopping work to reduce reloading cost.

- State: [Current project state, open files, last successful build/test]
- Resume Point: [The exact next action or prompt for Claude/Codex]
- Open Loops: [Unresolved bugs, unknowns, or decisions]

## Rituals

- [ ] Start Ritual: Sync git, read this dashboard, then hand `BUILD-PACKET.md` to Claude/Codex.
- [ ] End Ritual: Run safety checks, update this freeze summary, and save durable lessons.

## Why This Works

- Reduces heavy lifts by focusing attention on one Intermediate Packet.
- Externalizes context so the project state does not live in memory.
- Supports late starts by delaying decisions until useful information exists.
- Aligns AI assistants by making the current strategy explicit before execution.
