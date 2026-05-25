"""Feed watcher — polls subscribed RSS/Atom feeds and enqueues new entries.

One scanner serves three sources: generic RSS, subreddits (reddit.com/r/<sub>.rss),
and YouTube channels (youtube.com/feeds/videos.xml?channel_id=<id>). The per-feed
`kind` hint controls which input adapter processes the resulting entries.

State: `data/feed_seen.db` — (feed_url, entry_id) tuples. Dedup is per-feed so
subscribing to overlapping feeds doesn't re-process duplicate entries.

Run via:  `wikillm scan-feeds`
Schedule: add to cron alongside `wikillm scan`
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import httpx

from ..core import queue
from ..core.config import Config


SCHEMA = """
CREATE TABLE IF NOT EXISTS feed_seen (
    feed_url   TEXT NOT NULL,
    entry_id   TEXT NOT NULL,
    seen_at    REAL NOT NULL,
    PRIMARY KEY (feed_url, entry_id)
);
"""


def _db_path(config: Config) -> Path:
    return config.root / "data" / "feed_seen.db"


@contextmanager
def _connect(config: Config) -> Iterator[sqlite3.Connection]:
    p = _db_path(config)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(p, isolation_level=None)
    try:
        conn.executescript(SCHEMA)
        yield conn
    finally:
        conn.close()


def _seen(conn, feed_url: str, entry_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM feed_seen WHERE feed_url=? AND entry_id=? LIMIT 1",
        (feed_url, entry_id),
    ).fetchone()
    return row is not None


def _mark(conn, feed_url: str, entry_id: str) -> None:
    import time
    conn.execute(
        "INSERT OR IGNORE INTO feed_seen (feed_url, entry_id, seen_at) VALUES (?,?,?)",
        (feed_url, entry_id, time.time()),
    )


def _fetch_feed(url: str, user_agent: str, timeout_s: int) -> str:
    """Return the raw feed body; feedparser handles parsing."""
    headers = {"User-Agent": user_agent, "Accept": "application/atom+xml,application/rss+xml,application/xml;q=0.9,*/*;q=0.5"}
    with httpx.Client(follow_redirects=True, timeout=timeout_s, headers=headers) as client:
        resp = client.get(url)
    if resp.status_code >= 400:
        raise RuntimeError(f"GET {url} returned {resp.status_code}")
    return resp.text


def scan_feeds(config: Config) -> dict:
    """Poll every feed in `config.feeds`. Enqueue new entries. Return per-feed counters."""
    import feedparser  # lazy

    feeds = config.feeds  # list of {"url": ..., "kind": ...}
    if not feeds:
        return {"feeds": 0, "new_entries": 0, "by_feed": {}}

    by_feed: dict[str, int] = {}
    total_new = 0
    with _connect(config) as conn:
        for feed_cfg in feeds:
            feed_url = feed_cfg["url"]
            kind_hint = feed_cfg.get("kind", "url")
            try:
                body = _fetch_feed(feed_url, config.fetch_user_agent, config.fetch_timeout_s)
            except Exception as e:
                print(f"  ERR fetch {feed_url}: {e!r}")
                by_feed[feed_url] = 0
                continue

            parsed = feedparser.parse(body)
            if parsed.bozo and not parsed.entries:
                print(f"  WARN parse {feed_url}: {parsed.bozo_exception!r}")
                by_feed[feed_url] = 0
                continue

            feed_vault = feed_cfg.get("vault", "default")
            new_this_feed = 0
            for entry in parsed.entries:
                entry_id = (
                    entry.get("id")
                    or entry.get("guid")
                    or entry.get("link")
                    or entry.get("title", "")
                )
                if not entry_id:
                    continue
                if _seen(conn, feed_url, entry_id):
                    continue

                link = entry.get("link")
                if not link:
                    continue

                queue.enqueue_with_vault(config.inbox_db, kind_hint, link, None, feed_vault)
                _mark(conn, feed_url, entry_id)
                new_this_feed += 1

            by_feed[feed_url] = new_this_feed
            total_new += new_this_feed

    return {"feeds": len(feeds), "new_entries": total_new, "by_feed": by_feed}
