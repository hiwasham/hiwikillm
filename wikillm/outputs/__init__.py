"""Output layer — pluggable consumers of the knowledge layer.

To add a new output (weekly-digest-email, video-summary, podcast, dashboard, graph-viz,
slack-bot, discord-bot, RSS-feed-of-new-notes, ...):
1. Write a class with `name` and `serve(config, registry) -> None`
2. Import it here

Phase C: telegram_qa
Future: weekly_digest_email, video_summary (diffusion), podcast_generator (TTS),
        graph_viz, dashboard, rss_feed, slack_bot, discord_bot
"""
from . import cli_query      # noqa: F401  -- Phase C: pointer + synthesis Q&A via `wikillm ask`
from . import telegram_bot   # noqa: F401  -- Phase B: dedicated wikillm Telegram bot
