"""Resolves `Settings.ai_provider` to a concrete `AIProvider` (spec section
2). This is the ONLY place in the codebase that should import a concrete
provider class — every other module (Gateway, services, tests) depends on
the `AIProvider` Protocol, never on `OpenAIProvider`/`AnthropicProvider`
directly, so swapping/adding a provider never touches calling code."""

from __future__ import annotations

from app.ai.provider import AIProvider
from app.ai.providers.anthropic_provider import AnthropicProvider
from app.ai.providers.local_provider import LocalProvider
from app.ai.providers.openai_provider import OpenAIProvider
from app.core.config import Settings
from app.core.errors import AppError

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}


def build_provider(settings: Settings, *, provider_override: str | None = None) -> AIProvider:
    """`provider_override` lets a per-user `AISettings.provider_override`
    (spec section 48) win over the process-wide `AI_PROVIDER` env default."""
    provider_name = (provider_override or settings.ai_provider or "local").lower()

    if provider_name == "local":
        return LocalProvider()

    if provider_name == "openai":
        api_key = settings.ai_openai_api_key or settings.ai_api_key
        if not api_key:
            raise AppError(
                "AI_PROVIDER=openai but no API key is configured (AI_API_KEY / AI_OPENAI_API_KEY)."
            )
        return OpenAIProvider(
            api_key=api_key,
            model=settings.ai_model or DEFAULT_MODELS["openai"],
            base_url=settings.ai_openai_base_url,
            timeout_seconds=settings.ai_request_timeout_seconds,
            max_retries=settings.ai_max_retries,
        )

    if provider_name == "anthropic":
        api_key = settings.ai_anthropic_api_key or settings.ai_api_key
        if not api_key:
            raise AppError(
                "AI_PROVIDER=anthropic but no API key is configured (AI_API_KEY / AI_ANTHROPIC_API_KEY)."
            )
        return AnthropicProvider(
            api_key=api_key,
            model=settings.ai_model or DEFAULT_MODELS["anthropic"],
            base_url=settings.ai_anthropic_base_url,
            timeout_seconds=settings.ai_request_timeout_seconds,
            max_retries=settings.ai_max_retries,
        )

    raise AppError(f"Unknown AI_PROVIDER '{provider_name}'. Expected 'openai', 'anthropic', or 'local'.")
