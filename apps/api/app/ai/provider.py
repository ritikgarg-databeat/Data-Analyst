"""AI Provider abstraction (spec section 2). `AIProvider` is a `Protocol` —
the Gateway and every service depend on this interface, never a concrete SDK
or a hard-coded provider name. Implementations live in `app/ai/providers/*.py`;
`app/ai/providers/factory.py` resolves `Settings.ai_provider` to one of them.
Nothing outside the factory should import a concrete provider class."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class AIMessage:
    role: Role
    content: str


@dataclass(frozen=True)
class AIProviderUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class AIProviderResponse:
    text: str
    model: str
    usage: AIProviderUsage = field(default_factory=AIProviderUsage)
    finish_reason: str | None = None


class AIProviderError(Exception):
    """Any provider-level failure (network, timeout, malformed response,
    auth). Always caught by the Gateway and turned into a clean fallback
    message — never allowed to leak a stack trace or provider-internal detail
    to the frontend (spec section 45)."""


class AIProvider(Protocol):
    """The interface every provider implements. `generate` is synchronous —
    every caller in this codebase runs inside a sync FastAPI request handler
    (matching the rest of the app's services, none of which are `async def`),
    so providers use a plain `httpx.Client`, not `httpx.AsyncClient`."""

    name: str

    def generate(
        self,
        messages: list[AIMessage],
        *,
        max_tokens: int,
        temperature: float = 0.3,
    ) -> AIProviderResponse: ...
