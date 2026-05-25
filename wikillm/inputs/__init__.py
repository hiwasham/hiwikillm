"""Input layer — pluggable source adapters.

To add a new input (NotebookLM, RSS, subreddit, kindle-highlights, voice-memo, ...):
1. Write a class with `name`, `matches(ref, *, kind_hint=None)`, `fetch(config, item) -> str`
2. Import it here so `register_input` runs at package import

Phase A: url
Phase B: youtube, github, pdf, text, telegram_forward, drive_scan
Future: notebooklm, rss, subreddit, youtube_channel, email_imap, kindle_highlights,
        voice_memo, screenshots_folder, instapaper, pocket
"""
from . import url         # noqa: F401
from . import youtube     # noqa: F401
from . import github      # noqa: F401
from . import pdf         # noqa: F401
from . import text        # noqa: F401
