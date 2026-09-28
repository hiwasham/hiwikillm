# How to Add a Plugin

This guide shows how to extend `wikillm` without changing the core pipeline.

Plugins self-register when their module is imported. To activate a plugin, add its import to the layer package's `__init__.py`.

## Prerequisites

- You understand the target layer:
  - Inputs fetch source text.
  - Knowledge stages mutate `PipelineState`.
  - Outputs expose user-facing interfaces.
- `python3 -m wikillm list-plugins` works before you start.

## Add An Input Adapter

Create a file under `wikillm/inputs/`, for example `wikillm/inputs/rss_article.py`:

```python
from __future__ import annotations

from ..core.config import Config
from ..core.registry import register_input
from ..core.types import RawItem


class RSSArticleInput:
    name = "rss-article"

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        return kind_hint == self.name

    def fetch(self, config: Config, item: RawItem) -> str:
        return item.raw_payload or item.source_ref


register_input(RSSArticleInput())
```

Activate it in `wikillm/inputs/__init__.py`:

```python
from . import rss_article  # noqa: F401
```

Verify:

```bash
python3 -m wikillm list-plugins
```

```
➜  hiwikillm git:(main) ✗ python3 -m wikillm list-plugins
inputs:
  - github
  - pdf
  - text
  - url
  - youtube
knowledge stages (in order):
  - llm-distill
  - markdown-vault
  - milvus-index
  - entity-index
  - log-writer
outputs:
  - cli-query
```

The new adapter should appear under `inputs`.

## Add A Knowledge Stage

Create a file under `wikillm/knowledge/`, for example `wikillm/knowledge/tag_counter.py`:

```python
from __future__ import annotations

from ..core.config import Config
from ..core.registry import register_knowledge_stage
from ..core.types import PipelineState


class TagCounterStage:
    name = "tag-counter"

    def run(self, config: Config, state: PipelineState) -> None:
        if state.distilled is None:
            return
        state.artifacts["tag_counter_seen"] = True


register_knowledge_stage(TagCounterStage())
```

Activate it in `wikillm/knowledge/__init__.py` at the correct point in the ordered pipeline:

```python
from . import tag_counter  # noqa: F401
```

Order matters. A stage that needs `state.distilled.note_path` must run after `markdown-vault`.

Verify:

```bash
python3 -m wikillm list-plugins
```

The new stage should appear under `knowledge stages (in order)`.

## Add An Output Adapter

Create a file under `wikillm/outputs/`, for example `wikillm/outputs/weekly_digest.py`:

```python
from __future__ import annotations

from typing import Any

from ..core.config import Config
from ..core.registry import register_output


class WeeklyDigestOutput:
    name = "weekly-digest"

    def serve(self, config: Config, registry: Any = None) -> None:
        print("weekly digest would run here")


register_output(WeeklyDigestOutput())
```

Activate it in `wikillm/outputs/__init__.py`:

```python
from . import weekly_digest  # noqa: F401
```

Run it:

```bash
python3 -m wikillm serve weekly-digest
```

## Choose Names Carefully

Registry names must be unique inside each layer. These functions reject duplicate names:

- `register_input()`
- `register_output()`

Knowledge stages are stored as an ordered list and do not currently reject duplicate names, so pick distinct names manually.

## Keep Core Unchanged

Most plugin work should not touch:

- `wikillm/pipeline.py`
- `wikillm/core/registry.py`
- `wikillm/core/types.py`

Touch core only when the plugin protocol itself needs to change.

## Verification Checklist

Run:

```bash
python3 -m wikillm list-plugins
```

Then exercise the smallest path:

```bash
python3 -m wikillm distill "small test payload" --kind text
```

If your stage writes to [[Milvus]], entities, or note files, also inspect:

```bash
python3 -m wikillm stats
python3 -m wikillm entities --limit 10
```

## Troubleshooting

### The plugin does not appear in `list-plugins`

Check that the module is imported by the package `__init__.py`. Registration happens at import time.

### `detect_input` picks a different adapter

If `item.kind` exactly matches a registered input name, `detect_input()` uses that adapter first. Otherwise it probes adapters in insertion order and calls `matches()`.

### A knowledge stage sees `state.distilled is None`

Move the stage import after `llm_distill` in `wikillm/knowledge/__init__.py`, or guard and return when the note has not been created yet.

### A stage needs the note path

Move the stage import after `markdown_vault`, because `markdown-vault` writes the file and sets `state.distilled.note_path`.
