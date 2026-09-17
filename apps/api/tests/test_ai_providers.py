"""AI Provider tests (spec section 66: connection/timeout/retry/malformed
response). OpenAI/Anthropic providers are tested via `respx` mocking the
transport layer (see app/ai/providers/*.py's module docstrings for why
they're plain `httpx` clients, not the official SDKs — respx patches at the
transport layer regardless). LocalProvider needs no mocking: it makes no
network call at all."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.ai.provider import AIMessage, AIProviderError
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.factory import build_provider
from app.ai.providers.local_provider import LocalProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import Settings
from app.core.errors import AppError

_MESSAGES = [AIMessage(role="system", content="You are a coach."), AIMessage(role="user", content="Hello")]


class TestLocalProvider:
    def test_returns_a_deterministic_notice_and_no_usage(self) -> None:
        provider = LocalProvider()
        result = provider.generate(_MESSAGES, max_tokens=100)
        assert "local" in result.text.lower() or "AI_PROVIDER" in result.text
        assert result.model == "local"
        assert result.usage.input_tokens == 0
        assert result.usage.output_tokens == 0

    def test_echoes_the_users_message_without_analyzing_it(self) -> None:
        provider = LocalProvider()
        result = provider.generate(
            [AIMessage(role="user", content="why is my join duplicating rows")], max_tokens=100
        )
        assert "why is my join duplicating rows" in result.text


class TestOpenAIProvider:
    def _provider(self) -> OpenAIProvider:
        return OpenAIProvider(
            api_key="sk-test",
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            timeout_seconds=5.0,
            max_retries=1,
        )

    @respx.mock
    def test_successful_response_is_parsed(self) -> None:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "gpt-4o-mini",
                    "choices": [
                        {"message": {"role": "assistant", "content": "Hi there"}, "finish_reason": "stop"}
                    ],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 3},
                },
            )
        )
        result = self._provider().generate(_MESSAGES, max_tokens=100)
        assert result.text == "Hi there"
        assert result.model == "gpt-4o-mini"
        assert result.usage.input_tokens == 12
        assert result.usage.output_tokens == 3
        assert result.finish_reason == "stop"

    @respx.mock
    def test_auth_error_raises_ai_provider_error_with_the_real_message(self) -> None:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(401, json={"error": {"message": "Invalid API key"}})
        )
        with pytest.raises(AIProviderError, match="Invalid API key"):
            self._provider().generate(_MESSAGES, max_tokens=100)

    @respx.mock
    def test_malformed_response_raises_ai_provider_error(self) -> None:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"unexpected": "shape"})
        )
        with pytest.raises(AIProviderError):
            self._provider().generate(_MESSAGES, max_tokens=100)

    @respx.mock
    def test_timeout_raises_ai_provider_error(self) -> None:
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        with pytest.raises(AIProviderError, match="timed out|timeout"):
            self._provider().generate(_MESSAGES, max_tokens=100)

    @respx.mock
    def test_retries_on_server_error_then_succeeds(self) -> None:
        route = respx.post("https://api.openai.com/v1/chat/completions")
        route.side_effect = [
            httpx.Response(500, json={"error": {"message": "server error"}}),
            httpx.Response(
                200,
                json={
                    "model": "gpt-4o-mini",
                    "choices": [{"message": {"content": "Recovered"}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1},
                },
            ),
        ]
        result = self._provider().generate(_MESSAGES, max_tokens=100)
        assert result.text == "Recovered"
        assert route.call_count == 2


class TestAnthropicProvider:
    def _provider(self) -> AnthropicProvider:
        return AnthropicProvider(
            api_key="sk-ant-test",
            model="claude-haiku-4-5-20251001",
            base_url="https://api.anthropic.com/v1",
            timeout_seconds=5.0,
            max_retries=1,
        )

    @respx.mock
    def test_successful_response_is_parsed_and_system_prompt_is_split_out(self) -> None:
        route = respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "content": [{"type": "text", "text": "Hi there"}],
                    "usage": {"input_tokens": 10, "output_tokens": 4},
                    "stop_reason": "end_turn",
                },
            )
        )
        result = self._provider().generate(_MESSAGES, max_tokens=100)
        assert result.text == "Hi there"
        assert result.usage.input_tokens == 10
        assert result.usage.output_tokens == 4
        assert result.finish_reason == "end_turn"
        sent_body = route.calls.last.request.content
        assert b'"system":"You are a coach."' in sent_body or b'"system": "You are a coach."' in sent_body

    @respx.mock
    def test_error_response_raises_ai_provider_error(self) -> None:
        respx.post("https://api.anthropic.com/v1/messages").mock(
            return_value=httpx.Response(400, json={"error": {"message": "bad request"}})
        )
        with pytest.raises(AIProviderError, match="bad request"):
            self._provider().generate(_MESSAGES, max_tokens=100)


class TestProviderFactory:
    def test_local_needs_no_key(self) -> None:
        provider = build_provider(Settings(ai_provider="local"))
        assert provider.name == "local"

    def test_openai_without_a_key_raises_app_error(self) -> None:
        with pytest.raises(AppError, match="AI_API_KEY"):
            build_provider(Settings(ai_provider="openai"))

    def test_openai_with_a_key_builds_successfully(self) -> None:
        provider = build_provider(Settings(ai_provider="openai", ai_api_key="sk-test"))
        assert provider.name == "openai"

    def test_provider_override_wins_over_settings_default(self) -> None:
        provider = build_provider(
            Settings(ai_provider="openai", ai_api_key="sk-test"), provider_override="local"
        )
        assert provider.name == "local"

    def test_unknown_provider_raises_app_error(self) -> None:
        with pytest.raises(AppError, match="Unknown AI_PROVIDER"):
            build_provider(Settings(ai_provider="not-a-real-provider"))
