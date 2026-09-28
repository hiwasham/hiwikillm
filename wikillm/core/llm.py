"""Anthropic Messages client for the configured gateway (Claude via api.justwoker.icu)."""
from __future__ import annotations

import time

import httpx

from .config import Config


class LLMError(RuntimeError):
    pass


# HTTP statuses worth retrying — upstream-transient errors from API proxies.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# Anthropic API version pin (same as the header Claude Code sends).
_ANTHROPIC_VERSION = "2023-06-01"


def _split_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """Anthropic takes the system prompt as a top-level field, not a message.

    Pulls any ``system``-role messages out of the list, joins their content, and
    returns ``(system_text, remaining_messages)`` where the rest are user/assistant.
    """
    system_parts: list[str] = []
    rest: list[dict] = []
    for m in messages:
        if m.get("role") == "system":
            system_parts.append(m.get("content", ""))
        else:
            rest.append(m)
    return "\n\n".join(p for p in system_parts if p), rest


def chat(
    config: Config,
    *,
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout_s: float = 120.0,
    max_attempts: int = 3,
    backoff_base_s: float = 2.0,
) -> str:
    """Call the gateway's /messages (Anthropic Messages API). Retries transient errors.

    Retries on httpx.RequestError (network/DNS/timeout) and HTTP 429/5xx with
    exponential backoff (2s, 4s, 8s). Non-retryable status codes (4xx other than
    429) raise immediately so we don't spin on auth/permission errors.
    """
    url = f"{config.gateway_base_url}/messages"
    headers = {
        "x-api-key": config.gateway_token,
        "anthropic-version": _ANTHROPIC_VERSION,
        "Content-Type": "application/json",
    }
    system, convo = _split_system(messages)
    body: dict = {
        "model": model or config.model_distill,
        "messages": convo,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if system:
        body["system"] = system

    last_err: Exception | None = None
    for attempt in range(max_attempts):
        try:
            resp = httpx.post(url, headers=headers, json=body, timeout=timeout_s)
        except httpx.RequestError as e:
            last_err = LLMError(f"network error calling gateway: {e}")
            if attempt + 1 < max_attempts:
                time.sleep(backoff_base_s * (2 ** attempt))
                continue
            raise last_err from e

        if resp.status_code == 200:
            data = resp.json()
            try:
                blocks = data["content"]
                text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            except (KeyError, IndexError, TypeError) as e:
                raise LLMError(f"unexpected gateway response shape: {data}") from e
            if not text:
                raise LLMError(f"gateway returned no text content: {data}")
            return text

        if resp.status_code in _RETRYABLE_STATUS and attempt + 1 < max_attempts:
            time.sleep(backoff_base_s * (2 ** attempt))
            continue

        raise LLMError(f"gateway returned {resp.status_code}: {resp.text[:500]}")

    raise last_err or LLMError("gateway: exhausted retries with unknown error")
