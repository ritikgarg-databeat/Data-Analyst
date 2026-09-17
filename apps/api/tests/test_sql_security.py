"""Security tests for the SQL Lab: forbidden write/DDL operations, statement
stacking, query timeouts, row-limit enforcement, and isolation from the
application's own metadata tables (users/exercises/lessons/... must never be
queryable through the SQL Lab, which only ever registers views for a
Dataset's own registered SqlTable rows — see app/sql/registry.py)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.sql.safety import UnsafeQueryError, assert_safe_query
from app.sql.service import SqlExecutionService

FORBIDDEN_QUERIES = [
    "DELETE FROM orders",
    "UPDATE orders SET status = 'completed'",
    "INSERT INTO orders VALUES (1, 1, '2024-01-01', 'completed', 'web')",
    "DROP TABLE orders",
    "ALTER TABLE orders ADD COLUMN x INT",
    "TRUNCATE orders",
    "CREATE TABLE evil (x INT)",
    "ATTACH ':memory:' AS other",
    "COPY orders TO 'out.csv'",
    "PRAGMA database_list",
]


@pytest.mark.parametrize("query", FORBIDDEN_QUERIES)
def test_forbidden_write_and_admin_statements_are_rejected(client: TestClient, query: str) -> None:
    response = client.post(
        "/api/v1/sql/execute", json={"engine": "duckdb", "database": "ecommerce", "query": query}
    )

    assert response.status_code == 200  # execution failure is a normal (non-HTTP-error) result
    body = response.json()
    assert body["status"] == "error"
    assert "not allowed" in body["error"]["message"] or "read-only" in body["error"]["message"]


def test_multi_statement_stacking_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/sql/execute",
        json={"engine": "duckdb", "database": "ecommerce", "query": "SELECT 1; DELETE FROM orders"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert "single SQL statement" in body["error"]["message"]


def test_a_genuine_typo_surfaces_the_real_engine_parser_error_not_a_generic_denial(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/sql/execute",
        json={"engine": "duckdb", "database": "ecommerce", "query": "SELCT * FROM orders"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert "SELCT" in body["error"]["message"]  # the actual DuckDB parser error, not a fabricated message
    assert body["error"]["hint"]


def test_the_apps_own_metadata_tables_are_not_reachable_through_the_sql_lab(client: TestClient) -> None:
    for table in ["users", "exercises", "lessons", "exercise_attempts", "sql_query_history"]:
        response = client.post(
            "/api/v1/sql/execute",
            json={"engine": "duckdb", "database": "ecommerce", "query": f"SELECT * FROM {table}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        assert "does not exist" in body["error"]["message"]


def test_query_exceeding_the_timeout_is_cancelled_not_hung(db_session: Session) -> None:
    service = SqlExecutionService(
        db_session, settings=Settings(sql_lab_query_timeout_seconds=0.2, sql_lab_row_limit=1000)
    )

    result = service.execute(
        user_id="__test__",
        engine_name="duckdb",
        database_name="ecommerce",
        # A 200,000 x 200,000 row cross join is slow enough to reliably blow a 0.2s
        # budget without materializing enough data to be a resource risk.
        query="SELECT count(*) FROM range(200000) a, range(200000) b",
        log_history=False,
    )

    assert result.status == "error"
    assert "time limit" in result.error.message
    assert result.execution_time_ms < 2000


def test_row_limit_is_enforced_independent_of_the_requested_query(db_session: Session) -> None:
    service = SqlExecutionService(
        db_session, settings=Settings(sql_lab_query_timeout_seconds=10.0, sql_lab_row_limit=5)
    )

    result = service.execute(
        user_id="__test__",
        engine_name="duckdb",
        database_name="ecommerce",
        query="SELECT * FROM sessions",
        log_history=False,
    )

    assert result.status == "success"
    assert result.row_count == 5
    assert result.truncated is True


class TestArbitraryFileAccessIsBlocked:
    """Regression tests for a real, live-reproduced critical vulnerability:
    the DuckDB connection had no filesystem sandboxing at all, so a plain
    SELECT calling a file-reading table function (read_text/read_csv_auto/
    glob/...) could read (or, combined with EXPLAIN ANALYZE below, write)
    any file the API process could access — completely bypassing the
    keyword denylist, which never inspects function calls inside an
    otherwise-ordinary SELECT."""

    def test_reading_an_arbitrary_source_file_is_blocked(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "engine": "duckdb",
                "database": "ecommerce",
                "query": "SELECT * FROM read_text('app/core/config.py')",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        # The error message legitimately echoes back the requested filename
        # (from the query the user typed) -- what must never appear is any
        # actual file CONTENT, e.g. a real symbol defined in config.py.
        assert "class Settings" not in str(body)
        assert "disabled" in body["error"]["message"].lower()

    def test_reading_an_arbitrary_absolute_path_is_blocked(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "engine": "duckdb",
                "database": "ecommerce",
                "query": "SELECT * FROM read_csv_auto('C:/Windows/System32/drivers/etc/hosts')",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_registered_dataset_tables_still_query_normally(self, client: TestClient) -> None:
        """Disabling external access must not break the legitimate case —
        tables are materialized before it's disabled (see DuckDBEngine._connect)."""
        response = client.post(
            "/api/v1/sql/execute",
            json={"engine": "duckdb", "database": "ecommerce", "query": "SELECT COUNT(*) FROM orders"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["rows"][0][0] > 0


class TestExplainAnalyzeBypassIsBlocked:
    """Regression tests for a real, live-reproduced critical vulnerability:
    EXPLAIN ANALYZE genuinely executes its wrapped statement (unlike plain
    EXPLAIN), so wrapping any forbidden statement in it defeated the entire
    keyword denylist — confirmed live to create a table, write a new file to
    disk, and overwrite an existing file's content entirely."""

    def test_explain_analyze_is_rejected_outright(self) -> None:
        with pytest.raises(UnsafeQueryError, match="EXPLAIN ANALYZE"):
            assert_safe_query("EXPLAIN ANALYZE CREATE TABLE evil AS SELECT 1")

    def test_explain_analyze_wrapping_a_copy_is_rejected(self) -> None:
        with pytest.raises(UnsafeQueryError, match="EXPLAIN ANALYZE"):
            assert_safe_query("EXPLAIN ANALYZE COPY (SELECT 1) TO 'poc.csv'")

    def test_plain_explain_of_a_write_statement_is_still_rejected(self) -> None:
        with pytest.raises(UnsafeQueryError, match="CREATE"):
            assert_safe_query("EXPLAIN CREATE TABLE evil AS SELECT 1")

    def test_plain_explain_of_a_select_is_allowed(self) -> None:
        assert assert_safe_query("EXPLAIN SELECT * FROM orders") == "EXPLAIN SELECT * FROM orders"

    def test_explain_analyze_end_to_end_via_the_real_api_never_executes(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sql/execute",
            json={
                "engine": "duckdb",
                "database": "ecommerce",
                "query": "EXPLAIN ANALYZE CREATE TABLE poc_evil_table AS SELECT 1",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "error"

        # And the table genuinely was never created (a fresh connection per
        # execution means this also confirms no cross-request pollution).
        follow_up = client.post(
            "/api/v1/sql/execute",
            json={"engine": "duckdb", "database": "ecommerce", "query": "SELECT * FROM poc_evil_table"},
        )
        assert follow_up.json()["status"] == "error"


class TestQuoteAwareCommentAndStatementSplitting:
    """Regression tests: a naive regex-based comment-stripper/statement-
    splitter corrupted or falsely rejected legitimate single statements
    whose string literals happened to contain `--` or `;`."""

    def test_a_double_hyphen_inside_a_string_literal_is_not_treated_as_a_comment(self) -> None:
        query = "SELECT '10--20 off' AS discount_range"
        assert assert_safe_query(query) == query

    def test_a_semicolon_inside_a_string_literal_is_not_treated_as_a_statement_separator(self) -> None:
        query = "SELECT 'a;b' AS x"
        assert assert_safe_query(query) == query

    def test_a_real_trailing_comment_is_still_stripped(self) -> None:
        assert assert_safe_query("SELECT 1 -- a real comment\n") == "SELECT 1"

    def test_real_multi_statement_stacking_outside_any_string_is_still_rejected(self) -> None:
        with pytest.raises(UnsafeQueryError, match="single SQL statement"):
            assert_safe_query("SELECT 1; DELETE FROM orders")

    def test_end_to_end_via_the_real_api(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/sql/execute",
            json={"engine": "duckdb", "database": "ecommerce", "query": "SELECT '10--20 off' AS x"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["rows"][0][0] == "10--20 off"
