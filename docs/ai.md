# AI Layer

See [README.md](../README.md#ai-layer) for a one-paragraph summary and [`docs/roadmap.md`](roadmap.md)'s
Phase 10 entry for the full feature list. This page covers what a developer extending the AI layer
needs that the README doesn't spell out: the authority boundary, the mode system, and the prompt
registry.

## The one rule that matters most

**Deterministic wins. Always.** SQL correctness, Python test results, statistical/mathematical
calculations, dbt build/test results, data-modeling validation, every case/interview/exercise score,
mastery, and readiness number is computed by a real, deterministic engine elsewhere in this platform —
never by the AI layer. When AI is given such a result as context, it explains/coaches around it; it
never recomputes it, contradicts it, or states a different number. See `apps/api/app/ai/AUTHORITY.md`
for the full table (which feature owns which number).

Two "soft" AI-only observations are the deliberate exception, and are explicitly modeled as separate
from real scores so they can never be confused with them: **AI Mistake Memory** (`AIMistakeMemory`) and
**AI Skill Diagnosis** (`AISkillDiagnosis`) — neither is ever read by `MasteryService`, and neither
writes to `UserSkill.mastery_score`.

## Provider abstraction

`AIProvider` (protocol) → `LocalProvider` / `OpenAIProvider` / `AnthropicProvider`, resolved by
`app/ai/providers/factory.py` from `AI_PROVIDER`/`AI_MODEL`/`AI_API_KEY` env vars — nothing in
`app/ai/` hard-codes a provider name outside that one factory. `LocalProvider` is the zero-configuration
default: deterministic, no network, no key, and it never fabricates an answer — it says plainly that no
real provider is configured.

## The Gateway (`app/ai/gateway.py`)

The single choke point every AI feature calls through: Context Builder → Provider → Response Validator.
It never touches a database itself (callers pass already-fetched context in), and it never trusts a
provider's output blindly — a malformed/off-schema JSON response degrades to `structured_valid: false`
with the raw text still returned, never a crash and never a silently-accepted wrong shape.

## AI Modes (spec section 49)

Six personas, orthogonal to *which* feature is invoked — the same `SQL_REVIEW` feature answers
differently depending on mode:

| Mode | Stance |
|---|---|
| `TUTOR` | Teach — Socratic hint ladder before a direct answer |
| `COACH` | Guide — assume competence, focus on specific gaps |
| `REVIEWER` | Critique — direct about real issues |
| `INTERVIEWER` | Challenge — probe, withhold unasked-for information |
| `ANALYST` | Reason about given data without teaching or grading |
| `EXPLAINER` | Walk through what something does, step by step |

## Prompt registry (`app/ai/prompts/registry.py`)

One `PromptTemplate` per `AIFeature` value (version, purpose, input schema, output schema,
instructions) — a module-import-time `assert` fails the whole app if any `AIFeature` is missing its
template, so the registry can never silently drift out of sync with the enum. As of Phase 12 there are
29 features (the original 25 from Phase 10, plus `JD_EXTRACTION`/`RESUME_REVIEW`/`CAREER_COACH`/
`PORTFOLIO_REVIEW` from Phase 11). Adding a new AI capability means: add an `AIFeature` value, write one
`PromptTemplate` in its own module under `app/ai/prompts/`, register it — the Gateway, context builder,
and security layer need no changes.

## Context, security, and RAG

- `app/ai/context.py` — pure functions building small, bounded, per-feature payloads from real
  already-fetched domain objects. Never a database dump.
- `app/ai/security.py` — secret redaction, forbidden-key stripping, `<untrusted_data>` prompt-injection
  wrapping, applied automatically by the Gateway to every context payload and user message. See
  [`docs/security.md`](security.md) for the exact patterns.
- `app/ai/retrieval.py` — a local RAG (plain TF-IDF + cosine similarity over lesson content and the
  Metrics Library, computed with `numpy`; no vector database, no embedding API) grounding "Ask the
  Knowledge Base," with real citations and an explicit "I can't determine this" when nothing relevant
  is found.

## Cost controls

A daily request limit (`AI_DAILY_REQUEST_LIMIT`, default 200/user, overridable per-user in AI
Settings) is enforced before every dispatch; every call is written to `AIAuditLog` (feature, provider,
model, input/output tokens, latency, success, a redacted 300-char request preview — never the full
prompt). "AI usage today" in Settings reads this same counter.
