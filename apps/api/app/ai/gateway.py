"""AI Gateway (spec section 3): Frontend -> AI API -> AI Gateway -> Context
Builder -> AI Provider -> Response Validator -> Frontend. This module is the
ONLY code in the repo that calls `AIProvider.generate` directly (aside from
tests) — no router or frontend code may reach a provider except through
`call()` below.

Deliberately stateless / DB-free: it receives an already-built,
already-redacted context payload and returns a result; it never queries the
database and never persists anything (conversation/message/audit-log writes,
usage-limit checks, and settings resolution are the DB-aware service layer's
job — `app/services/ai_service.py`). This mirrors the
pure-engine-vs-DB-aware-service split `app/case_engine/` and
`app/interview_engine/` already established."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.ai.prompts.base import PromptTemplate
from app.ai.provider import AIMessage as ProviderMessage
from app.ai.provider import AIProvider, AIProviderError
from app.ai.security import redact_secrets, strip_forbidden_keys, truncate, wrap_untrusted_data

FALLBACK_MESSAGE = "I couldn't reach the AI provider just now. Please try again in a moment."


@dataclass(frozen=True)
class AIGatewayResult:
    text: str
    structured: dict | None
    structured_valid: bool
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int
    error: str | None = None


def build_context_message(context_payload: dict, *, max_chars: int) -> str:
    """Context Builder step's final output: a dict -> a redacted, size-capped,
    injection-defended string (spec section 4: "Only provide context relevant
    to the request... do NOT dump the entire database/profile")."""
    safe = strip_forbidden_keys(context_payload)
    rendered = json.dumps(safe, default=str, indent=2)
    rendered = truncate(rendered, max_chars)
    return wrap_untrusted_data("context", rendered)


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _validate_structured(text: str, schema: type[BaseModel] | None) -> tuple[dict | None, bool]:
    """Response Validator step. Never trusts the provider's output blindly
    (spec section 44) — a provider that returns malformed JSON, JSON that
    doesn't match the schema, or prose instead of JSON degrades to
    `structured=None, structured_valid=False` rather than raising, so a
    single bad response can never crash a request (spec section 45)."""
    if schema is None:
        return None, True
    candidate = _strip_code_fence(text)
    try:
        parsed = json.loads(candidate)
        validated = schema.model_validate(parsed)
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None, False
    return validated.model_dump(), True


def call(
    *,
    provider: AIProvider,
    template: PromptTemplate,
    context_payload: dict,
    user_message: str,
    system_prompt_override: str | None = None,
    conversation_history: list[ProviderMessage] | None = None,
    max_output_tokens: int,
    max_context_chars: int,
    mode: str | None = None,
) -> AIGatewayResult:
    system_prompt = system_prompt_override or template.render_system_prompt(mode=mode)
    context_message = build_context_message(context_payload, max_chars=max_context_chars)

    messages: list[ProviderMessage] = [ProviderMessage(role="system", content=system_prompt)]
    messages.append(ProviderMessage(role="user", content=context_message))
    if conversation_history:
        messages.extend(conversation_history)
    messages.append(ProviderMessage(role="user", content=redact_secrets(user_message)))

    started = time.monotonic()
    try:
        response = provider.generate(messages, max_tokens=max_output_tokens)
    except AIProviderError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return AIGatewayResult(
            text=FALLBACK_MESSAGE,
            structured=None,
            structured_valid=False,
            provider=getattr(provider, "name", "unknown"),
            model="unknown",
            input_tokens=None,
            output_tokens=None,
            latency_ms=latency_ms,
            error=str(exc),
        )
    latency_ms = int((time.monotonic() - started) * 1000)

    structured, structured_valid = _validate_structured(response.text, template.output_schema)
    display_text = response.text if structured is None else _summarize_structured(structured)

    return AIGatewayResult(
        text=display_text,
        structured=structured,
        structured_valid=structured_valid,
        provider=getattr(provider, "name", "unknown"),
        model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_ms=latency_ms,
    )


def _summarize_structured(structured: dict) -> str:
    """A structured response still needs *some* human-readable text (e.g. for
    AIMessage.content / a chat bubble) — prefer an explicit summary-shaped
    field if the schema has one, else a compact repr. The frontend always has
    the full `structured` dict too, so this is only a fallback display."""
    for key in ("summary", "diagnosis_summary", "interviewer_message", "answer", "overall_assessment"):
        if key in structured and isinstance(structured[key], str) and structured[key]:
            return structured[key]
    return json.dumps(structured, default=str)
