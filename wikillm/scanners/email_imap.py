"""IMAP email scanner (STUB — not yet implemented).

Polls a configured IMAP mailbox/label for emails matching a pattern (e.g. "Forwarded
to me", a specific label, or a tag), turns each into a RawItem, and enqueues. The
existing text/url adapters distill the body. The bot drains as usual.

Productive completion requires choices that are user-specific:

1. **Auth**: app password (Gmail) vs OAuth2 vs basic IMAP — depends on provider.
2. **Scope**: which mailbox/label/search query to watch? E.g. INBOX with a
   specific label like `wikillm-capture`, or a dedicated forwarding address.
3. **Idempotency**: store seen-message UIDs in `data/email_seen.db` per-account.
4. **Body extraction**: text/plain vs text/html (strip HTML), attachments?
5. **Dedup vs new-only**: only fetch UIDs above last-seen, or full re-scan with
   server-side filters.

Recommended path: dedicated label like `wikillm/` in Gmail, app password auth,
fetch text/plain bodies, dedup by UID. Run via cron alongside `scan` and
`scan-feeds`.

Config section to add to config.toml when implementing:
    [imap]
    server = "imap.gmail.com"
    port = 993
    username = "you@gmail.com"
    password_env_var = "WIKILLM_IMAP_PASSWORD"  # env var, not config.toml
    folder = "wikillm/"
    fetch_query = "UNSEEN"
"""
from __future__ import annotations

from ..core.config import Config


def scan_imap(config: Config) -> dict:
    """Stub — will poll IMAP and enqueue. See module docstring for impl path."""
    raise NotImplementedError(
        "IMAP scanner is a stub. To wire it: add [imap] config, choose auth + "
        "label, store WIKILLM_IMAP_PASSWORD in env, poll new UIDs, enqueue text. "
        "See module docstring for the design checklist."
    )
