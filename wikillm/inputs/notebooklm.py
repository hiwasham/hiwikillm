"""NotebookLM input adapter (STUB — not yet implemented).

The user has an existing browser-automation setup at `~/.notebooklm/` (Playwright
profiles + storage-state) that could be wired in. Productive completion requires
deciding HOW notebooklm contents enter the system:

Options to evaluate before implementing:

A. **Pull mode**: a scanner browses NotebookLM via the existing Playwright session,
   exports source documents + LLM-generated summaries, drops them into sources/.
   Pros: no new auth flow. Cons: brittle (Playwright + Google session expiration).

B. **Push mode**: user manually uses NotebookLM's "Export" feature; the exported
   file lands in Drive/wikillm/sources/ and wikillm picks it up via the existing
   scan. Zero new code. Just documentation.

C. **API mode**: as of 2026 there's no public NotebookLM API; this is blocked
   on Google releasing one. Long-tail.

For now this file exists so the architecture explicitly acknowledges NotebookLM as
a planned input, and so the registry knows it'll show up. To actually wire it,
pick A or B and replace the stub.
"""
from __future__ import annotations

from ..core.config import Config
from ..core.types import RawItem


class NotebookLMInput:
    name = "notebooklm"

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        # Match explicit kind hint only; no auto-detection until we wire a real fetcher.
        return kind_hint == "notebooklm"

    def fetch(self, config: Config, item: RawItem) -> str:
        raise NotImplementedError(
            "notebooklm input is a stub. See module docstring for implementation options. "
            "For now: use NotebookLM's export feature, drop the result into Drive sources/, "
            "and the existing pdf/text adapters handle it."
        )


# Not registered yet — uncomment when implemented:
# from ..core.registry import register_input
# register_input(NotebookLMInput())
