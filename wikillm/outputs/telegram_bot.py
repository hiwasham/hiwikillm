"""Telegram bot output — dedicated wikillm bot for /capture and /ask.

Uses Telegram's HTTP Bot API with long polling. Zero extra deps beyond httpx.
Auth: only `config.telegram_owner_ids` may use commands; everyone else gets a polite no.

Run via:
    python -m wikillm serve telegram-bot
"""
from __future__ import annotations

import time
import traceback
from typing import Any

import httpx

from ..core import queue
from ..core.config import Config
from ..core.registry import register_output
from ..core.types import RawItem


HELP_TEXT = """wikillm — your personal wiki-LLM.

/capture <url-or-text>   distill a source and add it to your wiki
/ask <question>          synthesized answer with citations
/find <query>            top-k matching notes (no LLM call)
/stats                   inbox status
/help                    show this message

You can also just paste a URL — I'll treat it as /capture.
"""


def _detect_kind(ref: str) -> str:
    # local copy to avoid importing wikillm.cli (which might have side effects)
    low = ref.lower()
    if low.startswith(("http://", "https://")):
        if "youtube.com/watch" in low or "youtu.be/" in low or "youtube.com/shorts/" in low:
            return "youtube"
        if "github.com/" in low:
            return "github"
        return "url"
    return "text"


class TelegramBotOutput:
    name = "telegram-bot"

    def serve(self, config: Config, registry: Any = None) -> None:
        if not config.telegram_bot_token:
            raise RuntimeError("config.telegram_bot_token is empty; set [telegram].bot_token in config.toml")
        api_base = f"https://api.telegram.org/bot{config.telegram_bot_token}"
        owner_ids = set(config.telegram_owner_ids)
        offset: int | None = None

        print(f"telegram-bot: polling started; owner_ids={owner_ids or '(open — no whitelist)'}")
        with httpx.Client(timeout=httpx.Timeout(connect=10.0, read=config.telegram_poll_timeout_s + 15.0, write=15.0, pool=15.0)) as client:
            while True:
                try:
                    params = {"timeout": config.telegram_poll_timeout_s}
                    if offset is not None:
                        params["offset"] = offset
                    resp = client.get(f"{api_base}/getUpdates", params=params)
                    if resp.status_code != 200:
                        print(f"telegram-bot: getUpdates {resp.status_code}: {resp.text[:200]}")
                        time.sleep(2)
                        continue
                    payload = resp.json()
                except (httpx.RequestError, ValueError) as e:
                    print(f"telegram-bot: poll error: {e!r}")
                    time.sleep(2)
                    continue

                for update in payload.get("result", []):
                    offset = update["update_id"] + 1
                    try:
                        self._handle_update(client, api_base, owner_ids, config, update)
                    except Exception:
                        traceback.print_exc()

    def _handle_update(self, client, api_base, owner_ids, config, update):
        msg = update.get("message") or update.get("channel_post") or update.get("edited_message") or {}
        text = (msg.get("text") or "").strip()
        if not text:
            return
        chat_id = msg.get("chat", {}).get("id")
        from_id = (msg.get("from") or {}).get("id")
        if chat_id is None:
            return

        if owner_ids and from_id not in owner_ids:
            self._send(client, api_base, chat_id,
                       f"sorry, this bot is private. your telegram id is {from_id}.")
            return

        # Bare URL? Treat as /capture
        if text.startswith(("http://", "https://")) and " " not in text.splitlines()[0]:
            self._handle_capture(client, api_base, chat_id, config, text)
            return

        cmd, _, rest = text.partition(" ")
        cmd = cmd.lower().lstrip("/")
        rest = rest.strip()

        if cmd in {"", "start", "help"}:
            self._send(client, api_base, chat_id, HELP_TEXT)
        elif cmd == "capture":
            if not rest:
                self._send(client, api_base, chat_id, "usage: /capture <url-or-text>")
                return
            self._handle_capture(client, api_base, chat_id, config, rest)
        elif cmd == "ask":
            if not rest:
                self._send(client, api_base, chat_id, "usage: /ask <question>")
                return
            self._handle_ask(client, api_base, chat_id, config, rest)
        elif cmd == "find":
            if not rest:
                self._send(client, api_base, chat_id, "usage: /find <query>")
                return
            self._handle_find(client, api_base, chat_id, config, rest)
        elif cmd == "stats":
            self._handle_stats(client, api_base, chat_id, config)
        else:
            # Unknown command — but if it looks like a question or text, treat as /ask
            if text.endswith("?") or len(text) > 30:
                self._handle_ask(client, api_base, chat_id, config, text)
            else:
                self._send(client, api_base, chat_id, f"unknown command /{cmd}. /help for list.")

    def _handle_capture(self, client, api_base, chat_id, config, ref):
        self._send_typing(client, api_base, chat_id)
        kind = _detect_kind(ref)
        payload = ref if kind == "text" else None
        item = RawItem(kind=kind, source_ref=ref, raw_payload=payload)
        try:
            from ..pipeline import process_one
            state = process_one(config, item)
            note_path = state.artifacts.get("note_path", "")
            chunks = state.artifacts.get("milvus_chunks", 0)
            title = state.distilled.title if state.distilled else "(no title)"
            self._send(
                client, api_base, chat_id,
                f"captured ({kind}): {title}\n→ {note_path}\nindexed {chunks} chunks",
            )
        except Exception as e:
            self._send(client, api_base, chat_id, f"capture failed: {e!r}")

    def _handle_ask(self, client, api_base, chat_id, config, question):
        self._send_typing(client, api_base, chat_id)
        try:
            from .cli_query import _hit_field, synthesis_query
            answer, hits = synthesis_query(config, question)
            if not hits:
                self._send(client, api_base, chat_id, answer)
                return
            seen: dict[str, int] = {}
            for h in hits:
                p = _hit_field(h, "note_path")
                if p and p not in seen:
                    seen[p] = len(seen) + 1
            src_lines = [f"  [{n}] {p.rsplit('/', 1)[-1]}" for p, n in sorted(seen.items(), key=lambda x: x[1])]
            self._send(client, api_base, chat_id, answer + "\n\nSources:\n" + "\n".join(src_lines))
        except Exception as e:
            self._send(client, api_base, chat_id, f"ask failed: {e!r}")

    def _handle_find(self, client, api_base, chat_id, config, query):
        self._send_typing(client, api_base, chat_id)
        try:
            from .cli_query import _hit_field, pointer_query
            hits = pointer_query(config, query)
            if not hits:
                self._send(client, api_base, chat_id, "(no matches)")
                return
            lines = []
            for i, h in enumerate(hits[:6], 1):
                title = _hit_field(h, "title", "(no title)")
                snippet = _hit_field(h, "text").strip().replace("\n", " ")[:160]
                lines.append(f"{i}. {title}\n   {snippet}...")
            self._send(client, api_base, chat_id, "\n\n".join(lines))
        except Exception as e:
            self._send(client, api_base, chat_id, f"find failed: {e!r}")

    def _handle_stats(self, client, api_base, chat_id, config):
        s = queue.stats(config.inbox_db)
        if not s:
            self._send(client, api_base, chat_id, "(inbox empty)")
            return
        self._send(client, api_base, chat_id, "Inbox:\n" + "\n".join(f"  {k}: {v}" for k, v in sorted(s.items())))

    @staticmethod
    def _send(client, api_base, chat_id, text):
        truncated = text[:4000] + ("\n…[truncated]" if len(text) > 4000 else "")
        try:
            client.post(
                f"{api_base}/sendMessage",
                json={"chat_id": chat_id, "text": truncated, "disable_web_page_preview": True},
                timeout=20.0,
            )
        except httpx.RequestError as e:
            print(f"telegram-bot: send failed: {e!r}")

    @staticmethod
    def _send_typing(client, api_base, chat_id):
        try:
            client.post(
                f"{api_base}/sendChatAction",
                json={"chat_id": chat_id, "action": "typing"},
                timeout=5.0,
            )
        except httpx.RequestError:
            pass


register_output(TelegramBotOutput())
