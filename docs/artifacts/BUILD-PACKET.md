---
project: "[[Project Name]]"
branch: "[Current Git Branch]"
type: "IP"
status: "#in-progress"
due_date: "YYYY-MM-DD"
---

# IP: [Title Of Specific Deliverable]

> Execution Rule: This file is for doing. If planning, tool research, or V2 ideas appear, move them to `DASHBOARD.md` or `BRAINSWEEP.md`.

## Scope Protection

Time is fixed. Energy is variable. Scope is the control knob. If capacity drops, reduce scope here instead of expanding the packet.

### ONLY Doing

- [ ] [Next actionable task with a verb]
- [ ] [Current bottleneck]

### NOT Doing

- [ ] [V2 feature idea]
- [ ] [Unrelated refactor]
- [ ] [Tooling/research rabbit hole]

## Archipelago Of Ideas

Do not start from a blank prompt. Paste existing islands of thought here: notes, snippets, prior research, links, working commands, screenshots, API examples, or half-written code.

- [[Note 1: Architecture patterns]]
- [Snippet: Previous working API call]
- [Research: NotebookLM or Second Brain synthesis]

Task for Claude/Codex:

```text
Build bridges between these islands while obeying Scope Protection. Ship the smallest useful version of this Intermediate Packet.
```

## Ugly First Draft

Use this section to break task-initiation paralysis. Spend 15 minutes producing a rough version: raw code, messy logic, UI sketch, checklist, failing test, or first-pass implementation.

```text
[Raw implementation notes go here.]
```

## Freeze Zone

Complete this before closing Claude/Codex or switching projects. This removes reloading cost for the next session.

- Where exactly I left off: [File name, line number, command output, or last error]
- Next 3 actionable steps:
  1. [Action 1]
  2. [Action 2]
  3. [Action 3]
- Open Questions: [Research or decisions needed next time]

## Rituals

- [ ] Start: Hand this file to Claude/Codex and say: "Follow the Scope Protection rules."
- [ ] Distraction: If a new idea appears, put it in `BRAINSWEEP.md` and keep executing.
- [ ] End: Run the relevant QA/check command, update the Freeze Zone, and commit or push if appropriate.

## Why This Works

- Reduces the wall of awful by lowering the starting bar with an Ugly First Draft.
- Avoids blank-prompt friction by assembling an Archipelago of Ideas first.
- Protects Return-on-Attention by keeping finite attention on the Critical Path.
- Makes work context-switch proof through the Freeze Zone.
