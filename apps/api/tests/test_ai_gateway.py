"""AI Gateway tests (spec sections 44-45): structured-output validation
never trusts the provider blindly, malformed/unparseable output degrades
gracefully instead of crashing, and a provider failure returns a clean
fallback message rather than leaking an exception."""

from __future__ import annotations

import json

from pydantic import BaseModel

from app.ai import gateway
from app.ai.prompts.base import PromptTemplate
from app.ai.provider import AIProviderError, AIProviderResponse


class _EchoStructuredResult(BaseModel):
    summary: str
    confidence: float = 0.5


class _FakeProvider:
    name = "fake"

    def __init__(self, response: AIProviderResponse | None = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error
        self.calls: list = []

    def generate(self, messages, *, max_tokens: int, temperature: float = 0.3):
        self.calls.append(messages)
        if self._error:
            raise self._error
        return self._response


def _template(output_schema=None) -> PromptTemplate:
    return PromptTemplate(
        feature="TEST_FEATURE",
        version="1.0",
        purpose="test",
        input_schema={},
        output_schema=output_schema,
        instructions="Be a helpful test assistant.",
    )


class TestStructuredValidation:
    def test_valid_json_matching_schema_is_validated(self) -> None:
        provider = _FakeProvider(
            AIProviderResponse(text=json.dumps({"summary": "ok", "confidence": 0.9}), model="fake")
        )
        result = gateway.call(
            provider=provider,
            template=_template(_EchoStructuredResult),
            context_payload={},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=1000,
        )
        assert result.structured_valid is True
        assert result.structured == {"summary": "ok", "confidence": 0.9}

    def test_json_wrapped_in_a_markdown_fence_is_still_parsed(self) -> None:
        text = "```json\n" + json.dumps({"summary": "fenced", "confidence": 0.5}) + "\n```"
        provider = _FakeProvider(AIProviderResponse(text=text, model="fake"))
        result = gateway.call(
            provider=provider,
            template=_template(_EchoStructuredResult),
            context_payload={},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=1000,
        )
        assert result.structured_valid is True
        assert result.structured["summary"] == "fenced"

    def test_malformed_json_degrades_to_invalid_without_raising(self) -> None:
        provider = _FakeProvider(AIProviderResponse(text="not json at all { broken", model="fake"))
        result = gateway.call(
            provider=provider,
            template=_template(_EchoStructuredResult),
            context_payload={},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=1000,
        )
        assert result.structured_valid is False
        assert result.structured is None

    def test_valid_json_not_matching_schema_degrades_to_invalid(self) -> None:
        provider = _FakeProvider(
            AIProviderResponse(text=json.dumps({"totally": "wrong shape"}), model="fake")
        )
        result = gateway.call(
            provider=provider,
            template=_template(_EchoStructuredResult),
            context_payload={},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=1000,
        )
        assert result.structured_valid is False

    def test_no_output_schema_never_attempts_json_parsing(self) -> None:
        provider = _FakeProvider(AIProviderResponse(text="just a normal reply, not JSON", model="fake"))
        result = gateway.call(
            provider=provider,
            template=_template(None),
            context_payload={},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=1000,
        )
        assert result.structured is None
        assert result.structured_valid is True
        assert result.text == "just a normal reply, not JSON"


class TestProviderFailureHandling:
    def test_provider_error_returns_a_clean_fallback_never_raises(self) -> None:
        provider = _FakeProvider(error=AIProviderError("boom: exploded"))
        result = gateway.call(
            provider=provider,
            template=_template(None),
            context_payload={},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=1000,
        )
        assert result.error is not None
        assert "boom" not in result.text  # internal error detail never leaks to the user-facing text
        assert result.text == gateway.FALLBACK_MESSAGE


class TestContextMessageBuilding:
    def test_context_is_wrapped_as_untrusted_data(self) -> None:
        message = gateway.build_context_message({"query": "SELECT 1"}, max_chars=1000)
        assert "<untrusted_data" in message
        assert "SELECT 1" in message

    def test_forbidden_keys_are_stripped_before_reaching_the_provider(self) -> None:
        provider = _FakeProvider(AIProviderResponse(text="ok", model="fake"))
        gateway.call(
            provider=provider,
            template=_template(None),
            context_payload={"api_key": "sk-shouldnotleak", "query": "SELECT 1"},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=1000,
        )
        sent_context_message = provider.calls[0][1].content  # [0] system, [1] context, [2] user
        assert "sk-shouldnotleak" not in sent_context_message
        assert "SELECT 1" in sent_context_message

    def test_context_is_truncated_to_the_configured_budget(self) -> None:
        provider = _FakeProvider(AIProviderResponse(text="ok", model="fake"))
        gateway.call(
            provider=provider,
            template=_template(None),
            context_payload={"blob": "x" * 5000},
            user_message="hi",
            max_output_tokens=100,
            max_context_chars=200,
        )
        sent_context_message = provider.calls[0][1].content
        assert len(sent_context_message) < 5000
        assert "truncated" in sent_context_message
