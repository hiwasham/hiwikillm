"""Plugin registry — the seam that makes inputs/knowledge/outputs dynamic.

Plugins register themselves at import time (in their package __init__). To add a new
input/knowledge-stage/output: write a class, drop it in the right package, add the
import line in that package's __init__.py. The CLI/pipeline never names plugins
directly — it goes through the registry.
"""
from __future__ import annotations

from .types import InputAdapter, KnowledgeStage, OutputAdapter, RawItem


INPUTS: dict[str, InputAdapter] = {}
KNOWLEDGE_STAGES: list[KnowledgeStage] = []
OUTPUTS: dict[str, OutputAdapter] = {}


def register_input(adapter: InputAdapter) -> None:
    if adapter.name in INPUTS:
        raise ValueError(f"input adapter {adapter.name!r} already registered")
    INPUTS[adapter.name] = adapter


def register_knowledge_stage(stage: KnowledgeStage) -> None:
    KNOWLEDGE_STAGES.append(stage)


def register_output(adapter: OutputAdapter) -> None:
    if adapter.name in OUTPUTS:
        raise ValueError(f"output adapter {adapter.name!r} already registered")
    OUTPUTS[adapter.name] = adapter


def detect_input(item: RawItem) -> InputAdapter:
    """Find the first input adapter that matches the given item. Raises if none do."""
    # If the item declares its kind explicitly and an adapter has that exact name,
    # prefer it. Otherwise fall back to .matches() probing.
    if item.kind in INPUTS:
        return INPUTS[item.kind]
    for adapter in INPUTS.values():
        if adapter.matches(item.source_ref, kind_hint=item.kind):
            return adapter
    raise KeyError(
        f"no input adapter handles kind={item.kind!r} ref={item.source_ref!r}; "
        f"registered: {sorted(INPUTS)}"
    )


def load_all() -> None:
    """Import every layer package so their plugins self-register."""
    # Imports inside this function to keep circular deps off the table.
    from .. import inputs       # noqa: F401
    from .. import knowledge    # noqa: F401
    from .. import outputs      # noqa: F401
