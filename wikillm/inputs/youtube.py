"""YouTube input adapter — fetches subtitles via yt-dlp + light VTT cleanup.

Output is title + channel + description + transcript text, ready for distillation.
Auto-generated captions are used when no manual subs exist.
"""
from __future__ import annotations

import re

import httpx

from ..core.config import Config
from ..core.registry import register_input
from ..core.types import RawItem


_YT_PATTERNS = ("youtube.com/watch", "youtu.be/", "youtube.com/shorts/", "youtube.com/live/")


def _looks_like_youtube(ref: str) -> bool:
    low = ref.lower()
    return any(p in low for p in _YT_PATTERNS)


def _strip_vtt(vtt: str) -> str:
    """VTT/SRT -> plain text, dedup adjacent duplicates (common in auto-captions)."""
    lines: list[str] = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if re.match(r"^\d+$", line):                # SRT cue index
            continue
        if "-->" in line:                           # timestamp
            continue
        line = re.sub(r"<[^>]+>", "", line)         # inline styling tags
        line = re.sub(r"&nbsp;", " ", line)
        lines.append(line)
    out: list[str] = []
    prev = None
    for L in lines:
        if L != prev:
            out.append(L)
            prev = L
    return "\n".join(out)


def _pick_track(tracks_by_lang: dict, langs=("en", "en-US", "en-GB")) -> list | None:
    for lang in langs:
        if tracks_by_lang.get(lang):
            return tracks_by_lang[lang]
    # last resort: first available
    for v in tracks_by_lang.values():
        if v:
            return v
    return None


def _track_vtt_url(track: list) -> str | None:
    if not track:
        return None
    for fmt in track:
        if fmt.get("ext") == "vtt":
            return fmt.get("url")
    return track[0].get("url")


class YouTubeInput:
    name = "youtube"

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        if kind_hint == "youtube":
            return True
        return _looks_like_youtube(ref)

    def fetch(self, config: Config, item: RawItem) -> str:
        import yt_dlp  # lazy
        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB"],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(item.source_ref, download=False)

        title = info.get("title") or item.source_ref
        uploader = info.get("uploader") or info.get("channel") or ""
        upload_date = info.get("upload_date") or ""
        duration = info.get("duration") or 0
        description = (info.get("description") or "").strip()

        track = _pick_track(info.get("subtitles") or {}) or _pick_track(info.get("automatic_captions") or {})
        transcript = ""
        url = _track_vtt_url(track) if track else None
        if url:
            try:
                with httpx.Client(follow_redirects=True, timeout=30) as client:
                    resp = client.get(url, headers={"User-Agent": config.fetch_user_agent})
                if resp.status_code == 200:
                    transcript = _strip_vtt(resp.text)
            except Exception:
                pass

        parts = [f"Title: {title}"]
        if uploader:
            parts.append(f"Channel: {uploader}")
        if upload_date:
            parts.append(f"Uploaded: {upload_date}")
        if duration:
            parts.append(f"Duration: {duration}s")
        if description:
            parts.append(f"\nDescription:\n{description}")
        parts.append(f"\nTranscript ({'manual' if (info.get('subtitles') or {}) else 'auto'}):\n"
                     + (transcript or "[no transcript available]"))
        return "\n".join(parts)


register_input(YouTubeInput())
