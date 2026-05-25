"""Entity canonicalization — merge variant `[[wikilinks]]` into canonical names.

The LLM curator emits free-form entity names — `[[Karpathy]]` and `[[Andrej Karpathy]]`
end up as separate nodes even though they're the same person. This module:

1. Lists all unique entities from `data/entities.db` (filled by the entity-index stage).
2. Sends them to the LLM in batches asking for a `variant -> canonical` mapping.
3. Persists the mapping to `data/canonical_entities.json` (incremental: existing
   mappings are preserved; only new entities are sent to the LLM on each run).
4. Optionally rewrites the notes on disk to use canonical names (`--apply`).

After `--apply`, run `wikillm backfill && wikillm backfill-entities` to refresh the
Milvus index and entity DB with the canonicalized text.
"""
from __future__ import annotations

import json
import re

from ..core.config import Config
from ..core.llm import chat
from ..knowledge.entity_index import all_entities


_LINK_RE = re.compile(r"\[\[([^\]\|]+?)(?:\|([^\]]*))?\]\]")
_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


SYSTEM = """You are an editor cleaning up entity names in a personal knowledge wiki.
Your job: group near-duplicate names into a canonical form."""


USER_TEMPLATE = """Below is a list of entities extracted as [[wikilinks]] from a personal
wiki. Many are near-duplicates: different casing, abbreviations, parenthetical disambiguators,
"the" prefix, full-name vs last-name, etc.

TASK: group them into canonical entities.

RULES:
- Pick ONE canonical name per group. Prefer the most complete, recognizable form a human
  would use in prose. For people: full name (e.g. "Andrej Karpathy" over "Karpathy").
  For companies: official short name (e.g. "OpenAI", not "OpenAI (company)").
  For technical terms: the most common form in the field.
- Only group entries that REFER TO THE SAME ENTITY. Different concepts must stay separate
  even when names look similar — for example "Tesla" the company and "Tesla" the SI unit
  must NOT merge unless an unambiguous disambiguator says they should.
- When uncertain, do NOT merge. Conservative > wrong.
- Output a JSON object mapping each entity (key) to its canonical form (value).
  Include identity mappings (canonical -> itself) so the canonical name appears as a key.
- Output ONLY the JSON object. No prose, no code fences, no commentary.

Entities to canonicalize:
{entities}
"""


def _mapping_path(config: Config):
    return config.root / "data" / "canonical_entities.json"


def load_mapping(config: Config) -> dict[str, str]:
    p = _mapping_path(config)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_mapping(config: Config, mapping: dict[str, str]) -> None:
    p = _mapping_path(config)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )


def propose_mapping(config: Config, entities: list[str], batch_size: int = 60) -> dict[str, str]:
    """Ask the LLM to canonicalize a list of entities, batched. Returns variant -> canonical."""
    mapping: dict[str, str] = {}
    for i in range(0, len(entities), batch_size):
        batch = entities[i : i + batch_size]
        prompt = USER_TEMPLATE.format(entities="\n".join(f"- {e}" for e in batch))
        try:
            response = chat(
                config,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=4096,
            )
        except Exception as e:
            print(f"  WARN: LLM call failed for batch starting at {i}: {e!r}")
            continue
        m = _JSON_BLOCK_RE.search(response)
        if not m:
            print(f"  WARN: no JSON block in LLM response for batch starting at {i}")
            continue
        try:
            batch_map = json.loads(m.group(0))
            if not isinstance(batch_map, dict):
                print(f"  WARN: LLM returned non-dict JSON for batch starting at {i}")
                continue
            mapping.update({str(k): str(v) for k, v in batch_map.items()})
        except json.JSONDecodeError as e:
            print(f"  WARN: JSON parse error for batch starting at {i}: {e}")
            continue
    return mapping


def _apply_to_markdown(md: str, mapping: dict[str, str]) -> tuple[str, int]:
    """Rewrite [[wikilinks]] using the mapping. Returns (new_md, links_changed)."""
    changes = 0

    def _repl(m: re.Match) -> str:
        nonlocal changes
        name = m.group(1).strip()
        canon = mapping.get(name)
        if canon and canon != name:
            changes += 1
            display = m.group(2)
            if display:
                return f"[[{canon}|{display}]]"
            return f"[[{canon}]]"
        return m.group(0)

    new_md = _LINK_RE.sub(_repl, md)
    return new_md, changes


def canonicalize(config: Config, *, apply: bool = False) -> dict:
    """Main entry. Returns counters."""
    seen = all_entities(config)  # [(name, count), ...]
    if not seen:
        return {
            "entities_seen": 0,
            "new_mappings_proposed": 0,
            "notes_rewritten": 0,
            "links_changed": 0,
        }

    existing = load_mapping(config)
    unmapped = [e for e, _ in seen if e not in existing]

    new_map: dict[str, str] = {}
    if unmapped:
        print(f"asking LLM to canonicalize {len(unmapped)} unmapped entities (batched)...")
        new_map = propose_mapping(config, unmapped)

    # Merge: existing wins on conflict (preserves human-edited mappings).
    full = dict(new_map)
    full.update(existing)
    save_mapping(config, full)

    notes_rewritten = 0
    links_changed = 0
    if apply:
        for p in sorted(config.notes_dir.rglob("*.md")):
            if p.name in {"index.md", "log.md"}:
                continue
            md = p.read_text(encoding="utf-8", errors="replace")
            new_md, count = _apply_to_markdown(md, full)
            if count > 0:
                p.write_text(new_md, encoding="utf-8")
                notes_rewritten += 1
                links_changed += count

    return {
        "entities_seen": len(seen),
        "new_mappings_proposed": len(new_map),
        "notes_rewritten": notes_rewritten,
        "links_changed": links_changed,
    }
