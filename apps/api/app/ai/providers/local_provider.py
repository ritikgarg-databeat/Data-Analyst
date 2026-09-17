"""The `local` provider (`AI_PROVIDER=local`, the default — spec's "AIProvider
├── LocalProvider (future)") — a deterministic, template-based responder that
needs no API key, no network access, and no third-party SDK. It exists for
three real reasons, not as a toy: (1) the platform must keep working with AI
"disabled" (spec section 5 — "Allow the user to disable AI"), (2) every AI
code path (Gateway → context → provider → validator) must be exercisable in
tests and in this development environment without a real external API key,
and (3) it must never pretend to be a real tutor — it says plainly that no AI
provider is configured, and it never fabricates an answer.

It does not "reason" — it cannot. Where a caller's context already contains
a concrete deterministic fact (e.g. a SQL error message, a failing dbt test
name), the local provider is allowed to surface that fact verbatim (never
inventing anything not already in the context), but it never generates new
analysis, code, or claims about data."""

from __future__ import annotations

from app.ai.provider import AIMessage, AIProviderResponse, AIProviderUsage

_UNAVAILABLE_NOTICE = (
    "AI is running in local (no-provider) mode, so I can't reason about this yet. "
    "Set AI_PROVIDER=openai or AI_PROVIDER=anthropic and a matching API key "
    "(see .env.example) to enable real AI tutoring, review, and coaching."
)


class LocalProvider:
    name = "local"

    def generate(
        self,
        messages: list[AIMessage],
        *,
        max_tokens: int,
        temperature: float = 0.3,
    ) -> AIProviderResponse:
        # No network call, no randomness, no invented content — see module
        # docstring. `max_tokens`/`temperature` are accepted only to satisfy
        # the AIProvider protocol; both are meaningless for a fixed reply.
        del max_tokens, temperature
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        text = _UNAVAILABLE_NOTICE
        if last_user.strip():
            text += f'\n\nYour message was received but not analyzed: "{last_user.strip()[:200]}"'
        return AIProviderResponse(text=text, model="local", usage=AIProviderUsage(0, 0), finish_reason="stop")
