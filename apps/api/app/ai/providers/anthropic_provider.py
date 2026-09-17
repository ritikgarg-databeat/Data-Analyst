"""Anthropic provider — a thin, direct `httpx` client against the Messages
REST API (`POST {base_url}/messages`). See `openai_provider.py`'s module
docstring for why this is raw `httpx` rather than the `anthropic` SDK.

Anthropic's wire format differs from OpenAI's in two ways this module has to
bridge: (1) the system prompt is a top-level `system` field, not a `"system"`-
role message inside `messages`; (2) a successful response's text lives in a
`content` list of typed blocks (`{"type": "text", "text": "..."}"`), not a
single string."""

from __future__ import annotations

import time

import httpx

from app.ai.provider import AIMessage, AIProviderError, AIProviderResponse, AIProviderUsage

_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self, *, api_key: str, model: str, base_url: str, timeout_seconds: float, max_retries: int
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

    def generate(
        self,
        messages: list[AIMessage],
        *,
        max_tokens: int,
        temperature: float = 0.3,
    ) -> AIProviderResponse:
        system_prompt = "\n\n".join(m.content for m in messages if m.role == "system")
        conversation = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": conversation,
        }
        if system_prompt:
            payload["system"] = system_prompt
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = client.post(f"{self._base_url}/messages", headers=headers, json=payload)
                if response.status_code >= 500 and attempt < self._max_retries:
                    time.sleep(min(2**attempt * 0.5, 4.0))
                    continue
                if response.status_code >= 400:
                    detail = _extract_error_message(response)
                    raise AIProviderError(f"Anthropic request failed ({response.status_code}): {detail}")
                return _parse_response(response.json(), fallback_model=self._model)
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise AIProviderError("Anthropic request timed out.") from exc
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise AIProviderError(f"Anthropic request failed: {exc}") from exc
            except ValueError as exc:
                # A 2xx response with a non-JSON body (e.g. a proxy/gateway in
                # front of the real API) — never let this escape as a raw,
                # uncaught crash; the Gateway's contract is to always degrade
                # to a clean fallback, never 500.
                raise AIProviderError(f"Anthropic returned an unparseable response: {exc}") from exc
        raise AIProviderError(f"Anthropic request failed after retries: {last_exc}")


def _extract_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
        return str(body.get("error", {}).get("message", response.text))[:300]
    except ValueError:
        return response.text[:300]


def _parse_response(body: dict, *, fallback_model: str) -> AIProviderResponse:
    try:
        blocks = body["content"]
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    except (KeyError, TypeError) as exc:
        raise AIProviderError("Anthropic response was missing an expected field.") from exc
    usage_raw = body.get("usage") or {}
    usage = AIProviderUsage(
        input_tokens=usage_raw.get("input_tokens"), output_tokens=usage_raw.get("output_tokens")
    )
    return AIProviderResponse(
        text=text, model=body.get("model", fallback_model), usage=usage, finish_reason=body.get("stop_reason")
    )
