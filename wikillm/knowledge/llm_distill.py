"""LLM distillation stage — raw source text -> structured Markdown DistilledNote."""
from __future__ import annotations

import datetime as dt
import re

from ..core.config import Config
from ..core.llm import chat
from ..core.registry import register_knowledge_stage
from ..core.types import DistilledNote, PipelineState


SYSTEM = """You are a personal-knowledge curator working on behalf of one user.
Your job: read a piece of source material and produce a Markdown "wiki note" the user
will keep in their personal knowledge base. The user is overwhelmed with information;
your notes are how they avoid drowning."""


USER_TEMPLATE = """Produce a single Markdown note for the source below.

REQUIRED STRUCTURE (in this exact order):

1. YAML frontmatter delimited by `---`, containing:
   - title: a concise descriptive title (string)
   - source: "{source}"
   - kind: "{kind}"
   - captured_at: "{captured_at}"
   - page_type: one of `Source`, `Entity`, `Concept`, `Comparison`, `Project` based on what the source PRIMARILY IS:
       * `Source` — most articles, blog posts, podcasts, videos. The default when in doubt.
       * `Entity` — a person, organization, product (their homepage, profile, about-page).
       * `Concept` — explains an idea, technique, or term in depth.
       * `Comparison` — compares two or more things ("X vs Y", roundups, reviews of multiple options).
       * `Project` — code repos, open-source projects, ongoing initiatives.
   - tags: a YAML list of 3-7 short kebab-case tags

2. `# <Title>` — repeat the title as an H1.

3. `> One-line description.` — a single blockquote sentence stating what this source is
   and why it might matter. Concrete, no filler.

4. `## TL;DR` — 3 to 7 bullets capturing the core content. Lossless on key points.

5. `## Key claims & findings` — the specific assertions, numbers, arguments, code patterns,
   or technical details worth remembering. Prefer concrete quotes/numbers over paraphrase.

6. `## Entities & links` — bullets of `[[entity]]` style wiki-links for people, papers,
   projects, products, technical terms the user might want to revisit. Use the exact
   names the source uses.

7. `## Open questions` — what the source raised but did not answer; things to dig into.

8. `## Source` — restate the source URL or path on its own line.

STYLE RULES:
- Lossless on key claims; lossy on examples and prose.
- Concrete > vague — keep specific numbers, names, quotes.
- No throat-clearing ("This article discusses...", "In summary...").
- No emojis. No section commentary.
- Output ONLY the Markdown note. No preamble, no code fences around the whole thing.

SOURCE METADATA
- source: {source}
- kind: {kind}
- captured_at: {captured_at}

SOURCE CONTENT (may be truncated; if so, do your best with what's there):
---
{content}
---
"""


_TITLE_RE = re.compile(r"^title:\s*(.+?)\s*$", re.MULTILINE)


def _slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return (s or "untitled")[:80]


class LLMDistillStage:
    name = "llm-distill"

    def run(self, config: Config, state: PipelineState) -> None:
        if state.source_text is None:
            raise RuntimeError("llm-distill: source_text is None")

        captured_at = dt.datetime.now(dt.timezone.utc)
        truncated = state.source_text[: config.distill_max_input_chars]
        prompt = USER_TEMPLATE.format(
            source=state.item.source_ref,
            kind=state.item.kind,
            captured_at=captured_at.isoformat(),
            content=truncated,
        )
        md = chat(
            config,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=4096,
        ).strip()

        if md.startswith("```"):
            md = re.sub(r"^```[a-zA-Z]*\n", "", md)
            md = re.sub(r"\n```\s*$", "", md)

        m = _TITLE_RE.search(md)
        title = m.group(1).strip().strip("\"'") if m else "Untitled"

        state.distilled = DistilledNote(
            markdown=md,
            title=title,
            slug=_slugify(title),
            raw_item=state.item,
            captured_at=captured_at,
        )


register_knowledge_stage(LLMDistillStage())
