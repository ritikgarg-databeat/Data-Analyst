"""AI Layer (Phase 10) DB-aware orchestration — mirrors the pure-engine-vs-
DB-aware-service split `app/case_engine/`+`app/services/case_service.py` and
`app/interview_engine/`+`app/services/interview_service.py` already
established. This service is the ONLY thing allowed to both call an existing
domain service (to fetch real, already-computed data) and the Gateway (to
get commentary about it) — see app/ai/AUTHORITY.md.

Covers: settings, usage/cost controls, conversation history, the Mentor,
Socratic hints, SQL/Python tutoring+review+debug+optimization, natural-
language-to-SQL/Python (generate-only, never auto-executed), analysis/
insight review, EDA assistance, the 6 domain coaches, and knowledge search
(RAG). Case/interview-specific coaching (Case Coach/Interviewer, Behavioral
Interviewer, Interview Debrief, communication coaching, the learning
planner, skill diagnosis, and project review) lives in
`app/services/ai_coach_service.py` to keep this file to a manageable size —
both share the `_dispatch` plumbing pattern below."""

from __future__ import annotations

import contextlib
from datetime import UTC, date, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai import context as ai_context
from app.ai import gateway
from app.ai.prompts.base import PromptTemplate
from app.ai.prompts.domain_coach import render_for_domain
from app.ai.prompts.registry import get_template
from app.ai.provider import AIMessage as ProviderMessage
from app.ai.providers.factory import build_provider
from app.ai.retrieval import search as retrieval_search
from app.ai.security import PRIVACY_NOTICE, redact_secrets
from app.ai.tools import AIToolbox
from app.core.config import Settings, get_settings
from app.core.errors import AppError, NotFoundError
from app.models.ai import (
    AIAuditLog,
    AIConversation,
    AIMessage,
    AIMistakeMemory,
    AISettings,
    AISkillDiagnosis,
    AIUsageCounter,
)
from app.models.enums import AIConversationRole, AIFeature
from app.models.exercise_attempt import ExerciseAttempt
from app.schemas.ai import (
    AIChatResponse,
    AIConversationListItemSchema,
    AIConversationSchema,
    AIKnowledgeAnswerResult,
    AIKnowledgeSource,
    AIMessageSchema,
    AIMistakeMemorySchema,
    AISettingsSchema,
    AISkillDiagnosisSchema,
    AIStructuredResponse,
    AIUsageResponse,
    UpdateAISettingsRequest,
)
from app.services.case_service import CaseService
from app.services.dataset_analysis_service import DatasetAnalysisService
from app.services.exercise_service import ExerciseService
from app.services.metrics_service import MetricsService
from app.services.skill_service import SkillService


class AIService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.exercises = ExerciseService(db)
        self.datasets = DatasetAnalysisService(db)
        self.skills = SkillService(db)
        self.metrics = MetricsService(db)
        self.cases = CaseService(db)
        from app.sql.service import SqlExecutionService

        self.sql = SqlExecutionService(db, self.settings)

    # --- Settings ------------------------------------------------------

    def _settings_row(self, user_id: str) -> AISettings:
        row = self.db.execute(select(AISettings).where(AISettings.user_id == user_id)).scalar_one_or_none()
        if row is None:
            row = AISettings(user_id=user_id)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
        return row

    def get_settings(self, user_id: str) -> AISettingsSchema:
        return self._to_settings_schema(self._settings_row(user_id))

    def update_settings(self, user_id: str, payload: UpdateAISettingsRequest) -> AISettingsSchema:
        row = self._settings_row(user_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
        self.db.commit()
        self.db.refresh(row)
        return self._to_settings_schema(row)

    def _to_settings_schema(self, row: AISettings) -> AISettingsSchema:
        effective_provider = row.provider_override or self.settings.ai_provider
        return AISettingsSchema(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            enabled=row.enabled,
            provider_override=row.provider_override,
            model_override=row.model_override,
            response_style=row.response_style,
            learning_mode=row.learning_mode,
            privacy_preference=row.privacy_preference,
            max_context_chars=row.max_context_chars,
            daily_request_limit=row.daily_request_limit,
            effective_provider=effective_provider,
            ai_configured=self.settings.ai_configured or effective_provider == "local",
        )

    # --- Usage / cost controls ------------------------------------------

    def _usage_counter(self, user_id: str, today: date) -> AIUsageCounter:
        row = self.db.execute(
            select(AIUsageCounter).where(
                AIUsageCounter.user_id == user_id, AIUsageCounter.usage_date == today
            )
        ).scalar_one_or_none()
        if row is not None:
            return row
        try:
            with self.db.begin_nested():
                row = AIUsageCounter(user_id=user_id, usage_date=today)
                self.db.add(row)
                self.db.flush()
        except IntegrityError:
            # Lost the create race to a concurrent request for the same user+day
            # (e.g. two open tabs both making the first AI call of the day) —
            # the row now exists; fetch the one that won instead of crashing.
            row = self.db.execute(
                select(AIUsageCounter).where(
                    AIUsageCounter.user_id == user_id, AIUsageCounter.usage_date == today
                )
            ).scalar_one()
        return row

    @staticmethod
    def _resolve_limit(ai_settings: AISettings, settings: Settings) -> int:
        # `or` would treat an explicit `daily_request_limit=0` (meaning "block
        # everything") as falsy and silently fall back to the global default.
        if ai_settings.daily_request_limit is not None:
            return ai_settings.daily_request_limit
        return settings.ai_daily_request_limit

    def get_usage_today(self, user_id: str) -> AIUsageResponse:
        ai_settings = self._settings_row(user_id)
        today = datetime.now(UTC).date()
        counter = self._usage_counter(user_id, today)
        limit = self._resolve_limit(ai_settings, self.settings)
        return AIUsageResponse(
            date=today,
            request_count=counter.request_count,
            input_tokens=counter.input_tokens,
            output_tokens=counter.output_tokens,
            daily_request_limit=limit,
            requests_remaining=max(0, limit - counter.request_count),
            privacy_notice=PRIVACY_NOTICE,
        )

    def _enforce_and_increment_usage(self, user_id: str, ai_settings: AISettings) -> AIUsageCounter:
        today = datetime.now(UTC).date()
        counter = self._usage_counter(user_id, today)
        limit = self._resolve_limit(ai_settings, self.settings)
        # An atomic compare-and-increment at the SQL level (never a Python-side
        # read-increment-write) — two near-simultaneous requests (e.g. two open
        # tabs) can no longer both read the same count, both increment in
        # memory, and have the second silently lose its update (or both slip
        # past the limit check before either commits).
        result = self.db.execute(
            update(AIUsageCounter)
            .where(AIUsageCounter.id == counter.id, AIUsageCounter.request_count < limit)
            .values(request_count=AIUsageCounter.request_count + 1)
        )
        if result.rowcount == 0:
            raise AppError(
                f"Daily AI request limit ({limit}) reached. Try again tomorrow, or raise the limit "
                "in AI Settings.",
                details={"code": "ai_daily_limit_reached"},
            )
        self.db.refresh(counter)
        return counter

    # --- Conversations ---------------------------------------------------

    def list_conversations(self, user_id: str) -> list[AIConversationListItemSchema]:
        rows = (
            self.db.execute(
                select(AIConversation)
                .where(AIConversation.user_id == user_id, AIConversation.is_archived.is_(False))
                .order_by(AIConversation.last_message_at.desc())
            )
            .scalars()
            .all()
        )
        return [
            AIConversationListItemSchema(
                id=r.id,
                created_at=r.created_at,
                updated_at=r.updated_at,
                feature=r.feature,
                title=r.title,
                context_type=r.context_type,
                context_id=r.context_id,
                is_archived=r.is_archived,
                last_message_at=r.last_message_at,
            )
            for r in rows
        ]

    def _get_conversation(self, user_id: str, conversation_id: str) -> AIConversation:
        row = self.db.get(AIConversation, conversation_id)
        if row is None or row.user_id != user_id:
            raise NotFoundError(f"Conversation '{conversation_id}' was not found.")
        return row

    def get_conversation(self, user_id: str, conversation_id: str) -> AIConversationSchema:
        row = self._get_conversation(user_id, conversation_id)
        return AIConversationSchema(
            id=row.id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            feature=row.feature,
            title=row.title,
            context_type=row.context_type,
            context_id=row.context_id,
            is_archived=row.is_archived,
            last_message_at=row.last_message_at,
            messages=[
                AIMessageSchema(
                    id=m.id,
                    role=m.role,
                    content=m.content,
                    structured_output=m.structured_output,
                    hint_level=m.hint_level,
                    created_at=m.created_at,
                )
                for m in row.messages
            ],
        )

    def delete_conversation(self, user_id: str, conversation_id: str) -> None:
        row = self._get_conversation(user_id, conversation_id)
        self.db.delete(row)
        self.db.commit()

    def _get_or_create_conversation(
        self,
        user_id: str,
        *,
        feature: str,
        conversation_id: str | None,
        context_type: str | None,
        context_id: str | None,
    ) -> AIConversation:
        if conversation_id:
            return self._get_conversation(user_id, conversation_id)
        conversation = AIConversation(
            user_id=user_id, feature=feature, context_type=context_type, context_id=context_id
        )
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def _history_as_provider_messages(
        self, conversation: AIConversation, *, limit: int = 20
    ) -> list[ProviderMessage]:
        recent = conversation.messages[-limit:]
        return [
            ProviderMessage(
                role="user" if m.role == AIConversationRole.USER else "assistant",
                # `gateway.call` only ever redacts the CURRENT turn's message —
                # history is spliced into the provider call verbatim, so a
                # secret typed in an earlier turn (stored as-is in
                # AIMessage.content) would otherwise be replayed unredacted to
                # the real provider on every later turn in the same conversation.
                content=redact_secrets(m.content),
            )
            for m in recent
        ]

    # --- Shared dispatch --------------------------------------------------

    def _dispatch(
        self,
        *,
        user_id: str,
        feature: str,
        context_payload: dict,
        user_message: str,
        mode: str | None = None,
        template: PromptTemplate | None = None,
        system_prompt_override: str | None = None,
        conversation: AIConversation | None = None,
        context_type: str | None = None,
    ):
        ai_settings = self._settings_row(user_id)
        if not ai_settings.enabled:
            raise AppError("AI is disabled in your AI Settings.", details={"code": "ai_disabled"})
        counter = self._enforce_and_increment_usage(user_id, ai_settings)

        provider = build_provider(self.settings, provider_override=ai_settings.provider_override)
        resolved_template = template or get_template(feature)
        max_context_chars = self.settings.ai_max_context_chars
        if ai_settings.max_context_chars:
            max_context_chars = min(max_context_chars, ai_settings.max_context_chars)

        history = self._history_as_provider_messages(conversation) if conversation else None

        result = gateway.call(
            provider=provider,
            template=resolved_template,
            context_payload=context_payload,
            user_message=user_message,
            system_prompt_override=system_prompt_override,
            conversation_history=history,
            max_output_tokens=self.settings.ai_max_output_tokens,
            max_context_chars=max_context_chars,
            mode=mode,
        )

        counter.input_tokens += result.input_tokens or 0
        counter.output_tokens += result.output_tokens or 0
        self.db.add(
            AIAuditLog(
                user_id=user_id,
                feature=feature,
                mode=mode,
                provider=result.provider,
                model=result.model,
                context_type=context_type,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                latency_ms=result.latency_ms,
                success=result.error is None,
                error_message=result.error,
                request_preview=redact_secrets(user_message)[:300],
            )
        )
        self.db.commit()
        return result, ai_settings

    def _chat_dispatch(
        self,
        *,
        user_id: str,
        feature: str,
        context_payload: dict,
        user_message: str,
        conversation_id: str | None,
        context_type: str | None,
        context_id: str | None,
        mode: str | None = None,
        hint_level: int | None = None,
        system_prompt_override: str | None = None,
    ) -> AIChatResponse:
        conversation = self._get_or_create_conversation(
            user_id,
            feature=feature,
            conversation_id=conversation_id,
            context_type=context_type,
            context_id=context_id,
        )
        self.db.add(
            AIMessage(conversation_id=conversation.id, role=AIConversationRole.USER, content=user_message)
        )
        result, _ = self._dispatch(
            user_id=user_id,
            feature=feature,
            context_payload=context_payload,
            user_message=user_message,
            mode=mode,
            conversation=conversation,
            context_type=context_type,
            system_prompt_override=system_prompt_override,
        )
        assistant_message = AIMessage(
            conversation_id=conversation.id,
            role=AIConversationRole.ASSISTANT,
            content=result.text,
            structured_output=result.structured,
            hint_level=hint_level,
        )
        self.db.add(assistant_message)
        conversation.last_message_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(assistant_message)
        return AIChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            reply=result.text,
            structured=result.structured,
            hint_level=hint_level,
            provider=result.provider,
            model=result.model,
            ai_configured=self.settings.ai_configured or result.provider == "local",
        )

    def _structured_dispatch(
        self,
        *,
        user_id: str,
        feature: str,
        context_payload: dict,
        user_message: str,
        mode: str | None = None,
        context_type: str | None = None,
        template: PromptTemplate | None = None,
        system_prompt_override: str | None = None,
    ) -> AIStructuredResponse:
        result, _ = self._dispatch(
            user_id=user_id,
            feature=feature,
            context_payload=context_payload,
            user_message=user_message,
            mode=mode,
            context_type=context_type,
            template=template,
            system_prompt_override=system_prompt_override,
        )
        return AIStructuredResponse(
            raw_text=result.text,
            structured=result.structured,
            structured_valid=result.structured_valid,
            provider=result.provider,
            model=result.model,
            ai_configured=self.settings.ai_configured or result.provider == "local",
        )

    # --- Mentor + Socratic hints ------------------------------------------

    def ask_mentor(
        self,
        user_id: str,
        *,
        message: str,
        context_type: str,
        context_id: str | None,
        conversation_id: str | None,
        mode: str,
    ) -> AIChatResponse:
        context_payload = self._build_mentor_context(user_id, context_type, context_id)
        return self._chat_dispatch(
            user_id=user_id,
            feature=AIFeature.MENTOR,
            context_payload=context_payload,
            user_message=message,
            conversation_id=conversation_id,
            context_type=context_type,
            context_id=context_id,
            mode=mode,
        )

    def _build_mentor_context(self, user_id: str, context_type: str, context_id: str | None) -> dict:
        if context_type == "case" and context_id:
            attempt = self.cases.get_attempt(user_id, context_id)
            return {
                "case": ai_context.build_case_public_context(attempt.case),
                "attempt": ai_context.build_case_attempt_context(attempt),
            }
        if context_type == "lesson" and context_id:
            from app.services.lesson_service import LessonService

            lesson = LessonService(self.db).get_by_slug(context_id)
            return {"lesson_title": lesson.title, "objectives": lesson.objectives}
        # sql/python/interview/general context is passed by the caller as
        # free text embedded in `message` for now (no exercise_slug/session
        # id is reliably available from a global launcher) — the frontend's
        # contextual "Ask AI" entry points (SQL/Python Lab, Case Workspace)
        # use the dedicated review/coach endpoints below instead, which do
        # carry real query/code/case context.
        return {}

    def send_hint(
        self,
        user_id: str,
        *,
        context_type: str,
        context_id: str,
        hint_level: int,
        conversation_id: str | None,
    ) -> AIChatResponse:
        """Progressive hint ladder (spec section 8). hint_level 1-3 = Hint
        1/2/3 (conceptual -> approach -> concrete); 4 = full Solution."""
        content = self.exercises.get_content(context_id, user_id)
        level_instruction = {
            1: "Give ONLY Hint 1: a conceptual direction, no specifics about syntax or approach.",
            2: "Give Hint 2: the general approach to take, still without writing any code/query.",
            3: "Give Hint 3: concrete guidance — name the specific function/clause/technique needed, "
            "but do not write the full solution.",
            4: "The learner asked for the solution. Give the full solution with an explanation "
            "of why it works.",
        }[hint_level]
        context_payload = {"exercise_prompt": content.prompt, "exercise_type": content.exercise_type}
        return self._chat_dispatch(
            user_id=user_id,
            feature=AIFeature.MENTOR,
            context_payload=context_payload,
            user_message=level_instruction,
            conversation_id=conversation_id,
            context_type=context_type,
            context_id=context_id,
            mode="TUTOR",
            hint_level=hint_level,
        )

    # --- SQL ---------------------------------------------------------------

    def _sql_schema_context(self, engine: str, database: str | None) -> list:
        if not database:
            return []
        try:
            tables = self.sql.list_tables(engine, database)
        except Exception:  # noqa: BLE001 — schema context is best-effort, never fatal
            return []
        schemas = []
        for t in tables[:15]:
            try:
                schemas.append(self.sql.get_table_schema(engine, database, t.table_name))
            except Exception:  # noqa: BLE001
                continue
        return schemas

    def review_sql(
        self, user_id: str, *, query: str, question: str | None, engine: str, database: str | None
    ) -> AIStructuredResponse:
        schemas = self._sql_schema_context(engine, database)
        context_payload = ai_context.build_sql_context(query=query, table_schemas=schemas)
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.SQL_REVIEW,
            context_payload=context_payload,
            user_message=question or "Review this query.",
            context_type="sql",
        )

    def debug_sql(
        self, user_id: str, *, query: str, error_message: str, engine: str, database: str | None
    ) -> AIStructuredResponse:
        schemas = self._sql_schema_context(engine, database)
        context_payload = ai_context.build_sql_context(
            query=query, table_schemas=schemas, error_message=error_message
        )
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.SQL_DEBUG,
            context_payload=context_payload,
            user_message="This query failed. Debug it.",
            context_type="sql",
        )

    def optimize_sql(
        self, user_id: str, *, query: str, engine: str, database: str | None, execution_time_ms: int | None
    ) -> AIStructuredResponse:
        schemas = self._sql_schema_context(engine, database)
        context_payload = ai_context.build_sql_context(
            query=query, table_schemas=schemas, execution_time_ms=execution_time_ms
        )
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.SQL_OPTIMIZATION,
            context_payload=context_payload,
            user_message="Coach me on the efficiency of this query.",
            context_type="sql",
        )

    def nl_to_sql(self, user_id: str, *, request: str, database: str, engine: str) -> AIStructuredResponse:
        schemas = self._sql_schema_context(engine, database)
        if not schemas:
            raise AppError(f"No known tables in database '{database}' to generate SQL against.")
        context_payload = {"schema": [_dump_schema(s) for s in schemas]}
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.NL_TO_SQL,
            context_payload=context_payload,
            user_message=request,
            context_type="sql",
        )

    def ask_sql_tutor(
        self,
        user_id: str,
        *,
        message: str,
        query: str,
        engine: str,
        database: str | None,
        conversation_id: str | None,
    ) -> AIChatResponse:
        schemas = self._sql_schema_context(engine, database)
        context_payload = ai_context.build_sql_context(query=query, table_schemas=schemas)
        return self._chat_dispatch(
            user_id=user_id,
            feature=AIFeature.SQL_TUTOR,
            context_payload=context_payload,
            user_message=message,
            conversation_id=conversation_id,
            context_type="sql",
            context_id=database,
            mode="TUTOR",
        )

    # --- Python --------------------------------------------------------

    def review_python(
        self,
        user_id: str,
        *,
        code: str,
        question: str | None,
        error_type: str | None,
        error_message: str | None,
        traceback_text: str | None,
    ) -> AIStructuredResponse:
        error = None
        if error_type or error_message:
            error = {"error_type": error_type, "message": error_message, "traceback_text": traceback_text}
        context_payload = ai_context.build_python_context(code=code, error=error)
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.PYTHON_REVIEW,
            context_payload=context_payload,
            user_message=question or "Review this code.",
            context_type="python",
        )

    def nl_to_python(self, user_id: str, *, request: str, dataset_slugs: list[str]) -> AIStructuredResponse:
        datasets_context = []
        for slug in dataset_slugs[:5]:
            try:
                datasets_context.append(self.datasets.get_raw_schema(slug, None).model_dump(mode="json"))
            except Exception:  # noqa: BLE001 — best-effort context
                continue
        context_payload = {"datasets": datasets_context}
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.NL_TO_PYTHON,
            context_payload=context_payload,
            user_message=request,
            context_type="python",
        )

    def ask_python_tutor(
        self,
        user_id: str,
        *,
        message: str,
        code: str,
        error_type: str | None,
        error_message: str | None,
        traceback_text: str | None,
        conversation_id: str | None,
    ) -> AIChatResponse:
        error = None
        if error_type or error_message:
            error = {"error_type": error_type, "message": error_message, "traceback_text": traceback_text}
        context_payload = ai_context.build_python_context(code=code, error=error)
        return self._chat_dispatch(
            user_id=user_id,
            feature=AIFeature.PYTHON_TUTOR,
            context_payload=context_payload,
            user_message=message,
            conversation_id=conversation_id,
            context_type="python",
            context_id=None,
            mode="TUTOR",
        )

    # --- Analysis / Insight / EDA ----------------------------------------

    def review_analysis(
        self,
        user_id: str,
        *,
        business_question: str,
        dataset_slug: str | None,
        code: str | None,
        findings: str | None,
    ) -> AIStructuredResponse:
        context_payload: dict = {"business_question": business_question}
        if dataset_slug:
            with contextlib.suppress(Exception):
                context_payload["dataset_metadata"] = self.datasets.get_raw_schema(
                    dataset_slug, None
                ).model_dump(mode="json")
        if code:
            context_payload["code"] = code
        if findings:
            context_payload["findings"] = findings
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.ANALYSIS_REVIEW,
            context_payload=context_payload,
            user_message="Review this analysis.",
            context_type="dataset",
        )

    def review_insight(
        self, user_id: str, *, observation: str, evidence: str, impact: str, recommendation: str
    ) -> AIStructuredResponse:
        context_payload = {
            "observation": observation,
            "evidence": evidence,
            "impact": impact,
            "recommendation": recommendation,
        }
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.INSIGHT_REVIEW,
            context_payload=context_payload,
            user_message="Evaluate this insight.",
            context_type="insight",
        )

    def eda_assist(
        self,
        user_id: str,
        *,
        dataset_id: str,
        table_name: str | None,
        explore: bool = False,
        user_goal: str | None = None,
    ) -> AIStructuredResponse:
        profile = self.datasets.get_profile(dataset_id)
        context_payload = ai_context.build_dataset_profile_context(profile)
        feature = AIFeature.DATA_EXPLORATION if explore else AIFeature.EDA_ASSISTANT
        if explore and user_goal:
            context_payload["user_goal"] = user_goal
        user_message = (
            (user_goal or "Propose a data-exploration plan for this dataset.")
            if explore
            else "Assist with EDA for this dataset."
        )
        return self._structured_dispatch(
            user_id=user_id,
            feature=feature,
            context_payload=context_payload,
            user_message=user_message,
            context_type="dataset",
        )

    # --- Domain coaches --------------------------------------------------

    def domain_coach(
        self, user_id: str, *, domain: str, question: str | None, result_ref: dict
    ) -> AIStructuredResponse:
        context_payload = ai_context.build_domain_result_context(result_ref, question=question)
        system_prompt = render_for_domain(domain)
        return self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.DOMAIN_COACH,
            context_payload=context_payload,
            user_message=question or f"Coach me on this {domain.lower()} result.",
            context_type=domain.lower(),
            system_prompt_override=system_prompt,
        )

    # --- Knowledge search (RAG) -------------------------------------------

    def search_knowledge(self, user_id: str, *, query: str, limit: int) -> AIKnowledgeAnswerResult:
        passages = retrieval_search(query, db=self.db, limit=limit)
        if not passages:
            return AIKnowledgeAnswerResult(
                answer="The platform's lessons and metric definitions don't cover this yet.",
                sources=[],
                insufficient_knowledge=True,
            )
        context_payload = {
            "retrieved_passages": [
                {
                    "title": p.title,
                    "kind": p.kind,
                    "lesson_slug": p.lesson_slug,
                    "module_slug": p.module_slug,
                    "domain_slug": p.domain_slug,
                    "text": p.text,
                }
                for p in passages
            ]
        }
        response = self._structured_dispatch(
            user_id=user_id,
            feature=AIFeature.KNOWLEDGE_SEARCH,
            context_payload=context_payload,
            user_message=query,
            context_type="knowledge",
        )
        if response.structured and response.structured_valid:
            return AIKnowledgeAnswerResult.model_validate(response.structured)
        return AIKnowledgeAnswerResult(
            answer=response.raw_text,
            sources=[
                AIKnowledgeSource(
                    title=p.title,
                    lesson_slug=p.lesson_slug,
                    module_slug=p.module_slug,
                    domain_slug=p.domain_slug,
                    kind=p.kind,
                )
                for p in passages
            ],
            insufficient_knowledge=False,
        )

    # --- Mistake memory ----------------------------------------------------

    def list_mistakes(self, user_id: str) -> list[AIMistakeMemorySchema]:
        rows = (
            self.db.execute(
                select(AIMistakeMemory)
                .where(AIMistakeMemory.user_id == user_id)
                .order_by(AIMistakeMemory.last_observed_at.desc())
            )
            .scalars()
            .all()
        )
        return [
            AIMistakeMemorySchema(
                id=r.id,
                created_at=r.created_at,
                updated_at=r.updated_at,
                skill_slug=r.skill_slug,
                category=r.category,
                mistake_summary=r.mistake_summary,
                first_observed_at=r.first_observed_at,
                last_observed_at=r.last_observed_at,
                occurrences=r.occurrences,
                recommended_review=r.recommended_review,
            )
            for r in rows
        ]

    def delete_mistake(self, user_id: str, mistake_id: str) -> None:
        row = self.db.get(AIMistakeMemory, mistake_id)
        if row is None or row.user_id != user_id:
            raise NotFoundError(f"Mistake memory '{mistake_id}' was not found.")
        self.db.delete(row)
        self.db.commit()

    def record_or_reinforce_mistake(
        self,
        user_id: str,
        *,
        skill_slug: str | None,
        category: str | None,
        mistake_summary: str,
        recommended_review: str | None,
    ) -> AIMistakeMemory:
        """Called by `ai_coach_service.diagnose_skill` when a diagnosis
        surfaces a recurring-looking issue — a simple exact-summary match
        against the user's existing memories, reinforcing (occurrences += 1)
        rather than duplicating."""
        existing = self.db.execute(
            select(AIMistakeMemory).where(
                AIMistakeMemory.user_id == user_id, AIMistakeMemory.mistake_summary == mistake_summary
            )
        ).scalar_one_or_none()
        if existing:
            existing.occurrences += 1
            existing.last_observed_at = datetime.now(UTC)
            if recommended_review:
                existing.recommended_review = recommended_review
            self.db.commit()
            return existing
        row = AIMistakeMemory(
            user_id=user_id,
            skill_slug=skill_slug,
            category=category,
            mistake_summary=mistake_summary,
            recommended_review=recommended_review,
        )
        self.db.add(row)
        self.db.commit()
        return row

    # --- Skill diagnosis (list side; generation lives in ai_coach_service) -

    def list_skill_diagnoses(
        self, user_id: str, *, skill_slug: str | None = None
    ) -> list[AISkillDiagnosisSchema]:
        stmt = select(AISkillDiagnosis).where(AISkillDiagnosis.user_id == user_id)
        if skill_slug:
            stmt = stmt.where(AISkillDiagnosis.skill_slug == skill_slug)
        rows = self.db.execute(stmt.order_by(AISkillDiagnosis.created_at.desc())).scalars().all()
        return [
            AISkillDiagnosisSchema(
                id=r.id,
                skill_slug=r.skill_slug,
                exercise_attempt_id=r.exercise_attempt_id,
                diagnosis=r.diagnosis,
                strength_areas=r.strength_areas,
                improvement_areas=r.improvement_areas,
                recommended_exercise_slugs=r.recommended_exercise_slugs,
                created_at=r.created_at,
            )
            for r in rows
        ]

    def _get_exercise_attempt(self, user_id: str, attempt_id: str) -> ExerciseAttempt:
        row = self.db.get(ExerciseAttempt, attempt_id)
        if row is None or row.user_id != user_id:
            raise NotFoundError(f"Exercise attempt '{attempt_id}' was not found.")
        return row

    def build_toolbox(self, user_id: str) -> AIToolbox:
        return AIToolbox(
            user_id=user_id,
            dataset_analysis_service=self.datasets,
            sql_execution_service=self.sql,
            skill_service=self.skills,
            case_service=self.cases,
            metrics_service=self.metrics,
        )


def _dump_schema(schema_obj) -> dict:
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(mode="json")
    if hasattr(schema_obj, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(schema_obj)
    return schema_obj.__dict__
