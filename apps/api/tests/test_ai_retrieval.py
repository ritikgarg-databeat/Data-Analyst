"""Lightweight local RAG retriever tests (spec sections 61-64, 66): relevant
content retrieval, and returning nothing when a query doesn't match the
platform's real content well enough (never falling back to a fabricated
answer from general knowledge)."""

from __future__ import annotations

from app.ai.retrieval import search


class TestRetrieval:
    def test_a_real_sql_question_retrieves_sql_lesson_content(self, db_session) -> None:
        results = search("SQL SELECT statement filtering rows with WHERE", db=db_session, limit=5)
        assert len(results) > 0
        assert any(r.kind == "lesson" for r in results)

    def test_results_are_ranked_by_relevance_descending(self, db_session) -> None:
        results = search("SQL window function OVER PARTITION BY", db=db_session, limit=10)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_gibberish_query_returns_no_passages(self, db_session) -> None:
        results = search("zzxqq flibbertigibbet nonexistent qwzxy", db=db_session, limit=5)
        assert results == []

    def test_empty_query_returns_no_passages(self, db_session) -> None:
        assert search("   ", db=db_session, limit=5) == []

    def test_respects_the_limit(self, db_session) -> None:
        results = search(
            "data analysis metric revenue customer statistics sql python", db=db_session, limit=2
        )
        assert len(results) <= 2

    def test_passages_carry_a_lesson_slug_for_citation(self, db_session) -> None:
        results = search("SQL SELECT statement filtering rows with WHERE", db=db_session, limit=5)
        lesson_results = [r for r in results if r.kind == "lesson"]
        assert lesson_results
        assert all(r.lesson_slug for r in lesson_results)
