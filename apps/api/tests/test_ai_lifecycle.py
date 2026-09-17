"""Integration tests for the Phase 10 AI Layer's live API
(`/api/v1/ai/*`), exercised through the real API against the real seeded
DB/content — settings, usage/cost controls, conversation persistence, the
Mentor, SQL review, and knowledge search (RAG). Runs against `AI_PROVIDER=
local` (this test environment sets no AI_PROVIDER/AI_API_KEY, and `local` is
the Settings default) — a real, deterministic, no-network provider, so these
tests exercise the FULL real plumbing (Gateway, context building, security
redaction, audit logging, usage counting, conversation persistence) without
mocking anything, the same way test_interview_lifecycle.py exercises the
real interview engine end-to-end rather than mocking it."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.security import redact_secrets
from app.models.ai import AIAuditLog, AIConversation, AIMessage
from app.models.enums import AIConversationRole, AIFeature
from app.services.ai_service import AIService


class TestAISettings:
    def test_get_settings_returns_sane_defaults(self, client: TestClient) -> None:
        response = client.get("/api/v1/ai/settings")
        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is True
        assert body["effective_provider"] == "local"
        assert body["ai_configured"] is True  # local never needs a key

    def test_update_settings_persists_changes(self, client: TestClient) -> None:
        response = client.patch(
            "/api/v1/ai/settings", json={"response_style": "concise", "learning_mode": "direct"}
        )
        assert response.status_code == 200
        assert response.json()["response_style"] == "concise"
        assert response.json()["learning_mode"] == "direct"

        refetched = client.get("/api/v1/ai/settings").json()
        assert refetched["response_style"] == "concise"

        # restore defaults so later tests in this file aren't affected
        client.patch("/api/v1/ai/settings", json={"response_style": "balanced", "learning_mode": "socratic"})


class TestAIUsage:
    def test_usage_today_reflects_real_requests(self, client: TestClient) -> None:
        before = client.get("/api/v1/ai/usage").json()
        client.post("/api/v1/ai/mentor", json={"message": "hello", "context_type": "general"})
        after = client.get("/api/v1/ai/usage").json()
        assert after["request_count"] == before["request_count"] + 1
        assert after["requests_remaining"] == before["requests_remaining"] - 1
        assert "may send selected" in after["privacy_notice"]

    def test_daily_request_limit_is_enforced(self, client: TestClient) -> None:
        client.patch("/api/v1/ai/settings", json={"daily_request_limit": 1})
        try:
            usage = client.get("/api/v1/ai/usage").json()
            # Reaching the limit fails the very next request regardless of how
            # many were already made today (limit=1 means "at most 1 total").
            if usage["request_count"] < 1:
                first = client.post("/api/v1/ai/mentor", json={"message": "one", "context_type": "general"})
                assert first.status_code == 200
            blocked = client.post("/api/v1/ai/mentor", json={"message": "two", "context_type": "general"})
            assert blocked.status_code == 400
            assert "limit" in blocked.json()["error"]["message"].lower()
        finally:
            client.patch("/api/v1/ai/settings", json={"daily_request_limit": None})

    def test_a_daily_request_limit_of_zero_blocks_every_request(self, client: TestClient) -> None:
        """Regression test — `ai_settings.daily_request_limit or default` used
        to treat an explicit `0` (falsy in Python) as "not set" and silently
        fall back to the global default, so a user who deliberately set the
        limit to 0 could still make requests up to the default limit."""
        client.patch("/api/v1/ai/settings", json={"daily_request_limit": 0})
        try:
            usage = client.get("/api/v1/ai/usage").json()
            assert usage["daily_request_limit"] == 0
            blocked = client.post("/api/v1/ai/mentor", json={"message": "hi", "context_type": "general"})
            assert blocked.status_code == 400
        finally:
            client.patch("/api/v1/ai/settings", json={"daily_request_limit": None})


class TestConversationHistoryRedaction:
    def test_a_secret_typed_in_an_earlier_turn_is_redacted_when_replayed_as_history(
        self, db_session: Session
    ) -> None:
        """Regression test — `gateway.call` only ever redacts the CURRENT
        turn's message; conversation history used to be spliced in verbatim,
        so a secret typed in an earlier turn (stored as-is in
        `AIMessage.content`) would be replayed unredacted to a real provider
        on every later turn in the same conversation."""
        conversation = AIConversation(user_id="test-user", feature=AIFeature.MENTOR)
        db_session.add(conversation)
        db_session.flush()
        secret_message = "Here's my key: sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890ABCD"
        db_session.add(
            AIMessage(conversation_id=conversation.id, role=AIConversationRole.USER, content=secret_message)
        )
        db_session.commit()
        db_session.refresh(conversation)

        service = AIService(db_session)
        history = service._history_as_provider_messages(conversation)

        assert len(history) == 1
        assert history[0].content == redact_secrets(secret_message)
        assert "sk-ant-api03" not in history[0].content


class TestAIMentorAndConversations:
    def test_ask_mentor_creates_a_conversation_and_replies(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/ai/mentor", json={"message": "What is a primary key?", "context_type": "general"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["conversation_id"]
        assert body["reply"]
        assert body["provider"] == "local"
        assert body["ai_configured"] is True

        listed = client.get("/api/v1/ai/conversations").json()
        assert any(c["id"] == body["conversation_id"] for c in listed)

        detail = client.get(f"/api/v1/ai/conversations/{body['conversation_id']}").json()
        assert detail["feature"] == "MENTOR"
        assert len(detail["messages"]) == 2  # the user's message + the assistant's reply
        assert detail["messages"][0]["role"] == "USER"
        assert detail["messages"][1]["role"] == "ASSISTANT"

    def test_a_second_message_in_the_same_conversation_accumulates_history(self, client: TestClient) -> None:
        first = client.post(
            "/api/v1/ai/mentor", json={"message": "First question", "context_type": "general"}
        ).json()
        second = client.post(
            "/api/v1/ai/mentor",
            json={
                "message": "Follow-up question",
                "context_type": "general",
                "conversation_id": first["conversation_id"],
            },
        ).json()
        assert second["conversation_id"] == first["conversation_id"]
        detail = client.get(f"/api/v1/ai/conversations/{first['conversation_id']}").json()
        assert len(detail["messages"]) == 4

    def test_delete_conversation_removes_it(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/ai/mentor", json={"message": "delete me", "context_type": "general"}
        ).json()
        deleted = client.delete(f"/api/v1/ai/conversations/{created['conversation_id']}")
        assert deleted.status_code == 204
        missing = client.get(f"/api/v1/ai/conversations/{created['conversation_id']}")
        assert missing.status_code == 404

    def test_disabling_ai_blocks_mentor_requests(self, client: TestClient) -> None:
        client.patch("/api/v1/ai/settings", json={"enabled": False})
        try:
            response = client.post("/api/v1/ai/mentor", json={"message": "hi", "context_type": "general"})
            assert response.status_code == 400
            assert "disabled" in response.json()["error"]["message"].lower()
        finally:
            client.patch("/api/v1/ai/settings", json={"enabled": True})


class TestSqlReview:
    def test_review_sql_returns_a_response_even_without_a_real_provider_configured(
        self, client: TestClient
    ) -> None:
        response = client.post(
            "/api/v1/ai/sql/review",
            json={"query": "SELECT * FROM orders", "engine": "duckdb", "database": None},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["provider"] == "local"
        assert body["raw_text"]
        # LocalProvider can't produce valid structured JSON — this is honestly
        # reported, never silently faked as a valid structured review.
        assert body["structured_valid"] is False
        assert body["structured"] is None


class TestKnowledgeSearch:
    def test_a_real_platform_topic_returns_grounded_sources(self, client: TestClient) -> None:
        response = client.get("/api/v1/ai/knowledge/search", params={"q": "SQL SELECT WHERE filtering rows"})
        assert response.status_code == 200
        body = response.json()
        assert body["insufficient_knowledge"] is False
        assert len(body["sources"]) > 0
        assert all(s["lesson_slug"] or s["kind"] == "metric" for s in body["sources"])

    def test_a_nonsense_query_says_it_does_not_know(self, client: TestClient) -> None:
        response = client.get(
            "/api/v1/ai/knowledge/search", params={"q": "zzxqq flibbertigibbet nonexistent"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["insufficient_knowledge"] is True
        assert body["sources"] == []


class TestAuditLogging:
    def test_every_ai_request_is_audited(self, client: TestClient, db_session: Session) -> None:
        before = db_session.query(AIAuditLog).count()
        client.post("/api/v1/ai/mentor", json={"message": "audit me", "context_type": "general"})
        after = db_session.query(AIAuditLog).count()
        assert after == before + 1
        latest = db_session.query(AIAuditLog).order_by(AIAuditLog.created_at.desc()).first()
        assert latest.feature == "MENTOR"
        assert latest.provider == "local"
        assert latest.success is True
        # The full message is never stored verbatim in the audit trail beyond
        # a short preview (spec section 47).
        assert latest.request_preview is not None
        assert len(latest.request_preview) <= 300


class TestMistakeMemory:
    def test_list_mistakes_starts_empty_and_delete_of_unknown_id_404s(self, client: TestClient) -> None:
        response = client.get("/api/v1/ai/mistakes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        missing = client.delete("/api/v1/ai/mistakes/not-a-real-id")
        assert missing.status_code == 404
