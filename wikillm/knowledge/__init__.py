"""Knowledge layer — pluggable stages over RawItem + source_text -> DistilledNote -> stored.

To add a new stage (entity-extract, milvus-index, graph-store, crewai-pipeline, ...):
1. Write a class with `name` and `run(config, state) -> None` (mutates state)
2. Import it here in the order you want stages to run

Phase A: llm_distill, markdown_vault
Phase C: milvus_index
Phase D: entity_link_extractor
Future: graph_store, crewai_pipeline, airflow_dag, dashboard_data
"""
from . import llm_distill      # noqa: F401  -- distills raw text into DistilledNote
from . import markdown_vault   # noqa: F401  -- writes DistilledNote to disk
from . import milvus_index     # noqa: F401  -- chunks + embeds + upserts into Milvus
