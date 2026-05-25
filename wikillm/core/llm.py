"""OpenAI-compatible client for the local OpenClaw gateway."""
from __future__ import annotations

import httpx

from .config import Config


class LLMError(RuntimeError):
    pass


def chat(
    config: Config,
    *,
    messages: list[dict],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 4096,
    timeout_s: float = 120.0,
) -> str:
    """Call the OpenClaw gateway's /chat/completions. Returns the assistant message text."""
    url = f"{config.gateway_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.gateway_token}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model or config.model_distill,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        resp = httpx.post(url, headers=headers, json=body, timeout=timeout_s)
    except httpx.RequestError as e:
        raise LLMError(f"network error calling gateway: {e}") from e

    if resp.status_code != 200:
        raise LLMError(f"gateway returned {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(f"unexpected gateway response shape: {data}") from e
