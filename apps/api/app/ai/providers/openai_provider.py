"""OpenAI provider — a thin, direct `httpx` client against the Chat
Completions REST API (`POST {base_url}/chat/completions`), not the `openai`
SDK. This keeps the dependency footprint to `httpx` (already used elsewhere
in this repo's test tooling, now promoted to a core dependency for this
exact purpose) instead of adding a second heavyweight SDK alongside
Anthropic's, and makes the wire format fully transparent and easy to mock in
tests (see tests/test_ai_providers.py, which uses `respx`)."""

from __future__ import annotations

import time

import httpx

from app.ai.provider import AIMessage, AIProviderError, AIProviderResponse, AIProviderUsage


class OpenAIProvider:
    name = "openai"

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
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = client.post(
                        f"{self._base_url}/chat/completions", headers=headers, json=payload
                    )
                if response.status_code >= 500 and attempt < self._max_retries:
                    time.sleep(min(2**attempt * 0.5, 4.0))
                    continue
                if response.status_code >= 400:
                    detail = _extract_error_message(response)
                    raise AIProviderError(f"OpenAI request failed ({response.status_code}): {detail}")
                return _parse_response(response.json(), fallback_model=self._model)
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise AIProviderError("OpenAI request timed out.") from exc
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt >= self._max_retries:
                    raise AIProviderError(f"OpenAI request failed: {exc}") from exc
            except ValueError as exc:
                # A 2xx response with a non-JSON body (e.g. a proxy/gateway in
                # front of the real API) — never let this escape as a raw,
                # uncaught crash; the Gateway's contract is to always degrade
                # to a clean fallback, never 500.
                raise AIProviderError(f"OpenAI returned an unparseable response: {exc}") from exc
        raise AIProviderError(f"OpenAI request failed after retries: {last_exc}")


def _extract_error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
        return str(body.get("error", {}).get("message", response.text))[:300]
    except ValueError:
        return response.text[:300]


def _parse_response(body: dict, *, fallback_model: str) -> AIProviderResponse:
    try:
        choice = body["choices"][0]
        text = choice["message"]["content"] or ""
        finish_reason = choice.get("finish_reason")
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderError("OpenAI response was missing an expected field.") from exc
    usage_raw = body.get("usage") or {}
    usage = AIProviderUsage(
        input_tokens=usage_raw.get("prompt_tokens"), output_tokens=usage_raw.get("completion_tokens")
    )
    return AIProviderResponse(
        text=text, model=body.get("model", fallback_model), usage=usage, finish_reason=finish_reason
    )
