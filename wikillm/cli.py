"""CLI entry point.

Common usage:
    python -m wikillm enqueue <ref> [--kind ...] [--vault NAME]
    python -m wikillm process [--once]
    python -m wikillm distill <ref> [--kind ...] [--vault NAME]
    python -m wikillm ask <question> [--mode pointer|synthesis] [--top-k N] [--vault NAME]
    python -m wikillm scan [--vault NAME]           # default: all vaults
    python -m wikillm scan-feeds                    # per-feed vault from config.toml
    python -m wikillm build-index [--vault NAME]    # default: "default"; pass --all for every vault
    python -m wikillm build-todos [--vault NAME]
    python -m wikillm backfill [--vault NAME] [--all]
    python -m wikillm backfill-entities [--vault NAME] [--all]
    python -m wikillm entities [--vault NAME]       # omit --vault to sum across all vaults
    python -m wikillm review [--count N]
    python -m wikillm reviewed <slug>
    python -m wikillm canonicalize [--apply]
    python -m wikillm vaults                        # list known vaults
    python -m wikillm list-plugins
    python -m wikillm stats
    python -m wikillm serve <output-name>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .core import queue
from .core.config import load_config
from .core.registry import INPUTS, KNOWLEDGE_STAGES, OUTPUTS, load_all
from .core.types import RawItem
from .core.vaults import DEFAULT_VAULT, list_vaults, vault_notes_dir
from .pipeline import process_one


def _detect_kind(ref: str) -> str:
    if ref.startswith(("http://", "https://")):
        low = ref.lower()
        if "youtube.com/watch" in low or "youtu.be/" in low:
            return "youtube"
        if "github.com/" in low:
            return "github"
        return "url"
    p = Path(ref)
    if p.exists() and p.is_file():
        return "pdf" if p.suffix.lower() == ".pdf" else "file"
    return "text"


def cmd_enqueue(args) -> int:
    cfg = load_config()
    kind = args.kind or _detect_kind(args.ref)
    payload = args.ref if kind == "text" else None
    row_id = queue.enqueue_with_vault(cfg.inbox_db, kind, args.ref, payload, args.vault)
    print(f"enqueued #{row_id} kind={kind} vault={args.vault}")
    return 0


def cmd_process(args) -> int:
    load_all()
    cfg = load_config()
    processed = 0
    while True:
        row = queue.claim_one(cfg.inbox_db)
        if row is None:
            if processed == 0:
                print("inbox empty")
            break
        try:
            item = RawItem(
                kind=row["kind"],
                source_ref=row["source_ref"],
                raw_payload=row["raw_payload"],
                vault=row["vault"] if "vault" in row.keys() else "default",
            )
            print(f"[#{row['id']}] processing kind={item.kind} vault={item.vault} ref={item.source_ref!r}")
            state = process_one(cfg, item)
            note_path = state.artifacts.get("note_path", "")
            chunks = state.artifacts.get("milvus_chunks", 0)
            queue.mark_done(cfg.inbox_db, int(row["id"]), note_path)
            print(f"[#{row['id']}] done -> {note_path}  (indexed {chunks} chunks)")
            processed += 1
            if args.once:
                break
        except Exception as e:
            queue.mark_error(cfg.inbox_db, int(row["id"]), repr(e))
            print(f"[#{row['id']}] ERROR: {e!r}", file=sys.stderr)
            if args.once:
                return 1
    return 0


def cmd_stats(args) -> int:
    cfg = load_config()
    s = queue.stats(cfg.inbox_db)
    if not s:
        print("inbox is empty")
    else:
        for k, v in sorted(s.items()):
            print(f"  {k:12s} {v}")
    return 0


def cmd_distill(args) -> int:
    load_all()
    cfg = load_config()
    kind = args.kind or _detect_kind(args.ref)
    payload = args.ref if kind == "text" else None
    item = RawItem(kind=kind, source_ref=args.ref, raw_payload=payload, vault=args.vault)
    state = process_one(cfg, item)
    print(state.artifacts.get("note_path", "(no note written)"))
    return 0


def cmd_list_plugins(args) -> int:
    load_all()
    print("inputs:")
    for name in sorted(INPUTS):
        print(f"  - {name}")
    print("knowledge stages (in order):")
    for stage in KNOWLEDGE_STAGES:
        print(f"  - {stage.name}")
    print("outputs:")
    if not OUTPUTS:
        print("  (none registered yet)")
    for name in sorted(OUTPUTS):
        print(f"  - {name}")
    return 0


def cmd_vaults(args) -> int:
    cfg = load_config()
    vaults = list_vaults(cfg)
    other_vault_dirs_for_default = {cfg.notes_dir / v for v in vaults if v != DEFAULT_VAULT}
    print(f"{len(vaults)} vault(s):")
    for v in vaults:
        n = vault_notes_dir(cfg, v)
        if not n.exists():
            count = 0
        else:
            count = 0
            for p in n.rglob("*.md"):
                if p.name in {"index.md", "log.md"}:
                    continue
                # for the default vault, exclude notes nested under named-vault subdirs
                if v == DEFAULT_VAULT and any(d in p.parents for d in other_vault_dirs_for_default):
                    continue
                count += 1
        marker = " (default)" if v == DEFAULT_VAULT else ""
        print(f"  {v}{marker}: {count} notes  [{n}]")
    return 0


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_KV_RE = re.compile(r'^(\w+):\s*"?([^"]*)"?\s*$')


def _parse_frontmatter(md: str) -> dict[str, str]:
    m = _FRONTMATTER_RE.match(md)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        km = _KV_RE.match(line)
        if km:
            out[km.group(1)] = km.group(2).strip()
    return out


def _backfill_one_vault(cfg, vault: str) -> int:
    from .knowledge.milvus_index import index_markdown
    notes_dir = vault_notes_dir(cfg, vault)
    if not notes_dir.exists():
        return 0
    other_vaults = {v for v in list_vaults(cfg) if v != vault and v != DEFAULT_VAULT}
    paths = []
    for p in sorted(notes_dir.rglob("*.md")):
        if p.name in {"index.md", "log.md"}:
            continue
        # When backfilling default, skip notes nested in named-vault dirs.
        if vault == DEFAULT_VAULT:
            try:
                top = p.relative_to(notes_dir).parts[0]
                if top in other_vaults:
                    continue
            except (ValueError, IndexError):
                pass
        paths.append(p)
    print(f"  vault {vault!r}: {len(paths)} notes")
    total = 0
    for p in paths:
        md = p.read_text(encoding="utf-8", errors="replace")
        meta = _parse_frontmatter(md)
        n = index_markdown(
            cfg,
            note_path=str(p),
            title=meta.get("title", p.stem),
            kind=meta.get("kind", "url"),
            source_ref=meta.get("source", str(p)),
            markdown=md,
            captured_at=meta.get("captured_at", ""),
            vault=vault,
        )
        print(f"    {p.relative_to(notes_dir)} -> {n} chunks")
        total += n
    return total


def cmd_backfill(args) -> int:
    load_all()
    cfg = load_config()
    vaults = list_vaults(cfg) if args.all else [args.vault]
    total = 0
    for v in vaults:
        total += _backfill_one_vault(cfg, v)
    print(f"done: {total} chunks across {len(vaults)} vault(s)")
    return 0


def _print_pointer_hits(hits: list[dict]) -> None:
    from .outputs.cli_query import _hit_field
    if not hits:
        print("(no hits)")
        return
    for i, h in enumerate(hits, 1):
        title = _hit_field(h, "title", "(no title)")
        path = _hit_field(h, "note_path")
        text = _hit_field(h, "text").strip().replace("\n", " ")
        distance = h.get("distance")
        score = f" (cosine {distance:.3f})" if isinstance(distance, (int, float)) else ""
        print(f"{i}. {title}{score}")
        print(f"   {path}")
        print(f"   {text[:240]}{'...' if len(text) > 240 else ''}")
        print()


def cmd_ask(args) -> int:
    load_all()
    cfg = load_config()
    from .outputs.cli_query import pointer_query, synthesis_query

    if args.mode == "pointer":
        hits = pointer_query(cfg, args.question, top_k=args.top_k, vault=args.vault)
        _print_pointer_hits(hits)
    else:
        answer, hits = synthesis_query(cfg, args.question, top_k=args.top_k, vault=args.vault)
        print(answer)
        print()
        if hits:
            from .outputs.cli_query import _hit_field
            print("Sources:")
            for i, h in enumerate(hits, 1):
                title = _hit_field(h, "title", "(no title)")
                path = _hit_field(h, "note_path")
                print(f"  [{i}] {title} — {path}")
    return 0


def cmd_serve(args) -> int:
    load_all()
    cfg = load_config()
    from .core.registry import OUTPUTS
    if args.output_name not in OUTPUTS:
        print(f"unknown output {args.output_name!r}; registered: {sorted(OUTPUTS)}", file=sys.stderr)
        return 1
    adapter = OUTPUTS[args.output_name]
    print(f"serving output: {adapter.name}")
    adapter.serve(cfg, None)
    return 0


def cmd_scan(args) -> int:
    """Scan sources_dir. Without --vault, scans every vault."""
    cfg = load_config()
    from .scanners.drive_sources import scan_sources_dir
    n = scan_sources_dir(cfg, vault=args.vault)
    scope = f"vault {args.vault!r}" if args.vault else "all vaults"
    print(f"scan complete ({scope}): {n} new item(s) enqueued")
    return 0


def cmd_scan_feeds(args) -> int:
    cfg = load_config()
    from .scanners.feed_watcher import scan_feeds
    result = scan_feeds(cfg)
    if result["feeds"] == 0:
        print("no feeds configured — add subscriptions to config.toml [feeds].subscriptions")
        return 0
    print(f"polled {result['feeds']} feeds, {result['new_entries']} new entries enqueued")
    for url, n in sorted(result["by_feed"].items()):
        if n > 0:
            print(f"  +{n}  {url}")
    return 0


def cmd_build_index(args) -> int:
    cfg = load_config()
    from .scanners.build_index import build_index
    vaults = list_vaults(cfg) if args.all else [args.vault]
    for v in vaults:
        out = build_index(cfg, vault=v)
        print(f"wrote {out}")
    return 0


def cmd_build_todos(args) -> int:
    cfg = load_config()
    from .scanners.build_todos import build_todos
    vaults = list_vaults(cfg) if args.all else [args.vault]
    for v in vaults:
        out = build_todos(cfg, vault=v)
        print(f"wrote {out}")
    return 0


def cmd_canonicalize(args) -> int:
    cfg = load_config()
    from .scanners.canonicalize import canonicalize
    result = canonicalize(cfg, apply=args.apply)
    print(f"entities seen:          {result['entities_seen']}")
    print(f"new mappings proposed:  {result['new_mappings_proposed']}")
    if args.apply:
        print(f"notes rewritten:        {result['notes_rewritten']}")
        print(f"links changed:          {result['links_changed']}")
        print("(re-run `wikillm backfill --all && wikillm backfill-entities --all` to refresh indices)")
    else:
        print(f"mapping saved to:       data/canonical_entities.json")
        print("(dry run — pass --apply to rewrite notes)")
    return 0


def cmd_review(args) -> int:
    cfg = load_config()
    from .scanners.review import get_due_summary
    due = get_due_summary(cfg, limit=args.count)
    if not due:
        print("(no notes due for review)")
        return 0
    print(f"{len(due)} note(s) due for review:\n")
    for d in due:
        print(f"  ▸ {d['title']}")
        try:
            rel = d['path'].relative_to(cfg.notes_dir)
        except ValueError:
            rel = d['path']
        print(f"    {rel}")
        if d['count'] == 0:
            print(f"    (never reviewed; first seen {d['overdue_days']:.0f} days ago)")
        else:
            print(f"    (reviewed {d['count']}x; overdue by {d['overdue_days']:.0f} days)")
        if d['tldr']:
            for line in d['tldr'].splitlines()[:5]:
                if line.strip():
                    print(f"      {line}")
        print()
    print(f"mark a note reviewed:  wikillm reviewed <slug-fragment>")
    return 0


def cmd_reviewed(args) -> int:
    cfg = load_config()
    from .scanners.review import find_note_by_slug, mark_reviewed
    matches = find_note_by_slug(cfg, args.slug)
    if not matches:
        print(f"no note matches slug fragment {args.slug!r}", file=sys.stderr)
        return 1
    if len(matches) > 1:
        print(f"multiple notes match {args.slug!r}:", file=sys.stderr)
        for m in matches:
            print(f"  - {m.name}", file=sys.stderr)
        return 1
    path = matches[0]
    count = mark_reviewed(cfg, str(path))
    print(f"marked reviewed: {path.name} (total reviews: {count})")
    return 0


def cmd_entities(args) -> int:
    cfg = load_config()
    from .knowledge.entity_index import all_entities
    vault = args.vault  # None means sum across all vaults
    rows = all_entities(cfg, vault=vault)
    if not rows:
        print("(no entities indexed yet — process some notes or run `backfill-entities`)")
        return 0
    width = max(len(name) for name, _ in rows[: args.limit])
    scope = f"vault {vault!r}" if vault else "all vaults"
    print(f"top {min(args.limit, len(rows))} entities ({scope}):")
    for name, n in rows[: args.limit]:
        print(f"  {name:<{width}}  {n}")
    return 0


def cmd_backfill_entities(args) -> int:
    cfg = load_config()
    from .knowledge.entity_index import index_entities_for_note
    vaults = list_vaults(cfg) if args.all else [args.vault]
    total_entities = 0
    total_notes = 0
    for v in vaults:
        notes_dir = vault_notes_dir(cfg, v)
        if not notes_dir.exists():
            continue
        other_vaults = {ov for ov in list_vaults(cfg) if ov != v and ov != DEFAULT_VAULT}
        print(f"vault {v!r}:")
        for p in sorted(notes_dir.rglob("*.md")):
            if p.name in {"index.md", "log.md"}:
                continue
            if v == DEFAULT_VAULT:
                try:
                    top = p.relative_to(notes_dir).parts[0]
                    if top in other_vaults:
                        continue
                except (ValueError, IndexError):
                    pass
            md = p.read_text(encoding="utf-8", errors="replace")
            n = index_entities_for_note(cfg, str(p), md, vault=v)
            print(f"  {p.relative_to(notes_dir)} -> {n} entities")
            total_entities += n
            total_notes += 1
    print(f"done: {total_entities} entity rows across {total_notes} notes in {len(vaults)} vault(s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wikillm")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_enq = sub.add_parser("enqueue", help="add a URL/path/text to the inbox")
    p_enq.add_argument("ref")
    p_enq.add_argument("--kind")
    p_enq.add_argument("--vault", default="default")
    p_enq.set_defaults(fn=cmd_enqueue)

    p_proc = sub.add_parser("process", help="drain the inbox")
    p_proc.add_argument("--once", action="store_true")
    p_proc.set_defaults(fn=cmd_process)

    p_stat = sub.add_parser("stats", help="show inbox counts by status")
    p_stat.set_defaults(fn=cmd_stats)

    p_d = sub.add_parser("distill", help="distill one item without using the queue")
    p_d.add_argument("ref")
    p_d.add_argument("--kind")
    p_d.add_argument("--vault", default="default")
    p_d.set_defaults(fn=cmd_distill)

    p_lp = sub.add_parser("list-plugins", help="show registered input/knowledge/output plugins")
    p_lp.set_defaults(fn=cmd_list_plugins)

    p_vlt = sub.add_parser("vaults", help="list known vaults and their note counts")
    p_vlt.set_defaults(fn=cmd_vaults)

    p_bf = sub.add_parser("backfill", help="re-index every note in a vault into Milvus")
    p_bf.add_argument("--vault", default="default")
    p_bf.add_argument("--all", action="store_true", help="backfill every known vault")
    p_bf.set_defaults(fn=cmd_backfill)

    p_ask = sub.add_parser("ask", help="ask a question over your indexed notes")
    p_ask.add_argument("question")
    p_ask.add_argument("--mode", choices=["pointer", "synthesis"], default="synthesis")
    p_ask.add_argument("--top-k", type=int, default=None)
    p_ask.add_argument("--vault", default="default")
    p_ask.set_defaults(fn=cmd_ask)

    p_srv = sub.add_parser("serve", help="run an output adapter's serve loop (blocks)")
    p_srv.add_argument("output_name", help="e.g. telegram-bot")
    p_srv.set_defaults(fn=cmd_serve)

    p_scan = sub.add_parser("scan", help="enqueue new files dropped into sources_dir")
    p_scan.add_argument("--vault", default=None, help="scan only this vault (default: all vaults)")
    p_scan.set_defaults(fn=cmd_scan)

    p_scanf = sub.add_parser("scan-feeds", help="poll RSS/Atom subscriptions and enqueue new entries")
    p_scanf.set_defaults(fn=cmd_scan_feeds)

    p_bi = sub.add_parser("build-index", help="write notes/index.md (TOC + top entities)")
    p_bi.add_argument("--vault", default="default")
    p_bi.add_argument("--all", action="store_true", help="rebuild index for every vault")
    p_bi.set_defaults(fn=cmd_build_index)

    p_bt = sub.add_parser("build-todos", help="write todos/index.md (open questions per note)")
    p_bt.add_argument("--vault", default="default")
    p_bt.add_argument("--all", action="store_true")
    p_bt.set_defaults(fn=cmd_build_todos)

    p_can = sub.add_parser("canonicalize", help="merge variant [[wikilinks]] into canonical names (LLM-driven)")
    p_can.add_argument("--apply", action="store_true", help="rewrite notes on disk (default: dry-run)")
    p_can.set_defaults(fn=cmd_canonicalize)

    p_rev = sub.add_parser("review", help="show notes due for spaced-repetition re-reading")
    p_rev.add_argument("--count", type=int, default=3)
    p_rev.set_defaults(fn=cmd_review)

    p_revd = sub.add_parser("reviewed", help="record that you re-read a note (matches by slug fragment)")
    p_revd.add_argument("slug")
    p_revd.set_defaults(fn=cmd_reviewed)

    p_ents = sub.add_parser("entities", help="list [[entities]] across notes by frequency")
    p_ents.add_argument("--limit", type=int, default=50)
    p_ents.add_argument("--vault", default=None, help="restrict to one vault (default: all vaults)")
    p_ents.set_defaults(fn=cmd_entities)

    p_bfe = sub.add_parser("backfill-entities", help="re-extract entities from every note")
    p_bfe.add_argument("--vault", default="default")
    p_bfe.add_argument("--all", action="store_true")
    p_bfe.set_defaults(fn=cmd_backfill_entities)

    args = p.parse_args(argv)
    return int(args.fn(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
