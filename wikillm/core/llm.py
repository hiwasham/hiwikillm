"""OpenAI-compatible client for the local OpenClaw gateway."""
from __future__ import annotations

import time

import httpx

from .config import Config


class LLMError(RuntimeError):
    pass


# HTTP statuses worth retrying — upstream-transient errors from API proxies.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


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
    """Call the gateway's /chat/completions. Retries transient upstream errors.

    Retries on httpx.RequestError (network/DNS/timeout) and HTTP 429/5xx with
    exponential backoff (2s, 4s, 8s). Non-retryable status codes (4xx other than
    429) raise immediately so we don't spin on auth/permission errors.
    """
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
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                raise LLMError(f"unexpected gateway response shape: {data}") from e

        if resp.status_code in _RETRYABLE_STATUS and attempt + 1 < max_attempts:
            time.sleep(backoff_base_s * (2 ** attempt))
            continue

        raise LLMError(f"gateway returned {resp.status_code}: {resp.text[:500]}")

    raise last_err or LLMError("gateway: exhausted retries with unknown error")
