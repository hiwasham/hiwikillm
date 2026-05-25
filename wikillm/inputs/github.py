"""GitHub input adapter — fetches README + top-level structure via GitHub REST API.

No auth required for public repos. For private repos set GH_TOKEN env var
(picked up automatically). Falls back gracefully if API rate-limits.
"""
from __future__ import annotations

import base64
import os
import re

import httpx

from ..core.config import Config
from ..core.registry import register_input
from ..core.types import RawItem


_REPO_RE = re.compile(r"^https?://github\.com/([^/]+)/([^/?#]+)(?:/.*)?$")


def _parse_repo(ref: str) -> tuple[str, str] | None:
    m = _REPO_RE.match(ref)
    if not m:
        return None
    owner = m.group(1)
    repo = m.group(2).rstrip(".git")
    if owner in {"orgs", "users", "settings", "marketplace"}:
        return None
    return owner, repo


class GitHubInput:
    name = "github"

    def matches(self, ref: str, *, kind_hint: str | None = None) -> bool:
        if kind_hint == "github":
            return True
        return _parse_repo(ref) is not None

    def fetch(self, config: Config, item: RawItem) -> str:
        parsed = _parse_repo(item.source_ref)
        if not parsed:
            raise ValueError(f"not a GitHub repo URL: {item.source_ref}")
        owner, repo = parsed

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": config.fetch_user_agent,
        }
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        with httpx.Client(follow_redirects=True, timeout=config.fetch_timeout_s, headers=headers) as client:
            meta_resp = client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if meta_resp.status_code == 404:
                raise RuntimeError(f"repo {owner}/{repo} not found")
            if meta_resp.status_code == 403:
                raise RuntimeError(
                    f"GitHub API rate-limited for {owner}/{repo}; set GH_TOKEN to lift the limit"
                )
            if meta_resp.status_code != 200:
                raise RuntimeError(f"GitHub API repo {owner}/{repo}: {meta_resp.status_code}")
            meta = meta_resp.json()

            readme_text = ""
            readme_resp = client.get(f"https://api.github.com/repos/{owner}/{repo}/readme")
            if readme_resp.status_code == 200:
                content = readme_resp.json().get("content", "")
                try:
                    readme_text = base64.b64decode(content).decode("utf-8", errors="replace")
                except Exception:
                    pass

            tree_text = ""
            default_branch = meta.get("default_branch") or "main"
            tree_resp = client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}",
                params={"recursive": "0"},
            )
            if tree_resp.status_code == 200:
                entries = tree_resp.json().get("tree", [])
                tree_text = "\n".join(f"{e['path']} ({e['type']})" for e in entries[:300])

        parts = [
            f"Repo: {owner}/{repo}",
            f"URL: https://github.com/{owner}/{repo}",
            f"Description: {meta.get('description') or '(none)'}",
            f"Stars: {meta.get('stargazers_count')}  Forks: {meta.get('forks_count')}",
            f"Primary language: {meta.get('language') or '?'}",
            f"Default branch: {meta.get('default_branch')}",
            f"License: {(meta.get('license') or {}).get('spdx_id') or 'none'}",
            f"Topics: {', '.join(meta.get('topics', []) or []) or '(none)'}",
            f"Homepage: {meta.get('homepage') or '(none)'}",
            "",
            "=== README ===",
            readme_text or "(no README)",
            "",
            "=== Top-level structure ===",
            tree_text or "(unable to fetch tree)",
        ]
        return "\n".join(parts)


register_input(GitHubInput())
