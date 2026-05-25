"""Orchestrator — runs one RawItem through input fetch + knowledge stages."""
from __future__ import annotations

from .core.config import Config
from .core.registry import KNOWLEDGE_STAGES, detect_input
from .core.types import PipelineState, RawItem


def process_one(config: Config, item: RawItem) -> PipelineState:
    """Drive a RawItem through the input layer and all registered knowledge stages."""
    state = PipelineState(item=item)

    adapter = detect_input(item)
    state.source_text = adapter.fetch(config, item)

    if not KNOWLEDGE_STAGES:
        raise RuntimeError(
            "no knowledge stages registered — did wikillm.core.registry.load_all() run?"
        )

    for stage in KNOWLEDGE_STAGES:
        stage.run(config, state)

    return state
