"""Integration tests for the real-execution Excel exercise grading pipeline
(`/api/v1/excel/*`), exercised through the real API against the authored
`excel-sumif-region-totals` exercise — content loading -> real formula
evaluation (app/excel_lab/formula_engine.py) -> check-cell comparison ->
scoring -> ExerciseAttempt/ExcelExerciseTestResult persistence -> mastery
side effects, exactly like test_sql_exercises_integration.py does for SQL."""

from fastapi.testclient import TestClient

SLUG = "excel-sumif-region-totals"


def _starter_sheets(client: TestClient) -> list[dict]:
    content = client.get(f"/api/v1/excel/exercises/{SLUG}").json()
    return content["starter_sheets"]


def test_excel_exercise_content_never_leaks_the_solution(client: TestClient) -> None:
    response = client.get(f"/api/v1/excel/exercises/{SLUG}")

    assert response.status_code == 200
    body = response.json()
    assert body["check_cells"] == ["Summary!B2", "Summary!B3"]
    assert any(s["name"] == "Data" for s in body["starter_sheets"])
    assert "solution" not in body
    assert "excel_solution_sheets" not in body


def test_rejecting_a_non_excel_exercise_slug(client: TestClient) -> None:
    response = client.get("/api/v1/excel/exercises/aov-query")  # a SQL exercise
    assert response.status_code == 400


def test_evaluate_preview_computes_formulas_live_with_no_persistence(client: TestClient) -> None:
    response = client.post(
        "/api/v1/excel/evaluate",
        json={"sheets": [{"name": "Sheet1", "cells": {"A1": "10", "A2": "20", "A3": "=A1+A2"}}]},
    )
    assert response.status_code == 200
    sheet = response.json()["sheets"][0]
    assert sheet["cells"]["A3"] == 30.0


def test_submitting_the_correct_workbook_passes_and_scores_100(client: TestClient) -> None:
    sheets = _starter_sheets(client)
    for sheet in sheets:
        if sheet["name"] == "Summary":
            sheet["cells"]["B2"] = "=SUMIF(Data!A2:A6,A2,Data!B2:B6)"
            sheet["cells"]["B3"] = "=SUMIF(Data!A2:A6,A3,Data!B2:B6)"

    response = client.post(f"/api/v1/excel/exercises/{SLUG}/submit", json={"submitted_sheets": sheets})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PASSED"
    assert body["score"] == 100.0
    assert body["passed"] is True
    assert body["explanation"]
    summary_cells = next(s["cells"] for s in body["evaluated_sheets"] if s["name"] == "Summary")
    assert summary_cells["B2"] == 300.0
    assert summary_cells["B3"] == 450.0


def test_submitting_a_wrong_formula_fails_and_hides_the_explanation(client: TestClient) -> None:
    sheets = _starter_sheets(client)
    for sheet in sheets:
        if sheet["name"] == "Summary":
            sheet["cells"]["B2"] = "999"  # hardcoded literal, not a recomputing formula, and wrong
            sheet["cells"]["B3"] = "999"

    response = client.post(f"/api/v1/excel/exercises/{SLUG}/submit", json={"submitted_sheets": sheets})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILED"
    assert body["passed"] is False
    assert body["explanation"] is None
    assert any(not o["passed"] for o in body["test_outcomes"])
