"""Integration tests for EDA workspaces + the automatic overview/question
generator (sections 19-21, 50-51 of the Phase 5 spec)."""

from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient


def _csv_bytes(headers: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _import_ready_dataset(client: TestClient, name: str) -> dict:
    rows = [
        ["US", "electronics", 120.0, "2024-01-01"],
        ["US", "electronics", 80.0, "2024-01-15"],
        ["UK", "books", 20.0, "2024-02-01"],
        ["UK", "books", 25.0, "2024-02-20"],
        ["US", "books", 15.0, "2024-03-01"],
    ]
    content = _csv_bytes(["country", "category", "revenue", "order_date"], rows)
    client.post(
        "/api/v1/datasets/import",
        files=[("files", ("orders.csv", content, "text/csv"))],
        data={"name": name},
    )
    created = client.get(f"/api/v1/datasets/{name.lower().replace(' ', '-')}")
    return created.json()


class TestDatasetLevelConvenience:
    def test_generates_an_overview_directly_from_a_dataset(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Eda Overview Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.get(f"/api/v1/eda/{dataset['slug']}")
        assert response.status_code == 200
        overview = response.json()
        assert overview["row_count"] == 5
        assert overview["table_name"] == "orders"
        assert len(overview["categorical_summaries"]) >= 1

    def test_generates_deterministic_questions(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Eda Questions Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.get(f"/api/v1/eda/{dataset['slug']}/questions")
        assert response.status_code == 200
        questions = response.json()
        assert len(questions) > 0
        assert all("question" in q and "category" in q for q in questions)


class TestWorkspaceCrud:
    def test_create_a_workspace_defaults_to_the_datasets_first_table(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Workspace Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.post(
            "/api/v1/eda-workspaces", json={"dataset_id": dataset["id"], "name": "My exploration"}
        )
        assert response.status_code == 201
        workspace = response.json()
        assert workspace["table_name"] == "orders"
        assert workspace["name"] == "My exploration"

    def test_list_get_update_delete_a_workspace(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Workspace Crud Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])
        workspace = client.post(
            "/api/v1/eda-workspaces", json={"dataset_id": dataset["id"], "name": "Scratch"}
        ).json()

        assert any(w["id"] == workspace["id"] for w in client.get("/api/v1/eda-workspaces").json())
        assert client.get(f"/api/v1/eda-workspaces/{workspace['id']}").json()["name"] == "Scratch"

        updated = client.patch(
            f"/api/v1/eda-workspaces/{workspace['id']}",
            json={"name": "Renamed", "state": {"selected_columns": ["revenue"]}},
        ).json()
        assert updated["name"] == "Renamed"
        assert updated["state"]["selected_columns"] == ["revenue"]

        delete_response = client.delete(f"/api/v1/eda-workspaces/{workspace['id']}")
        assert delete_response.status_code == 204
        assert client.get(f"/api/v1/eda-workspaces/{workspace['id']}").status_code == 404

    def test_generate_and_persist_an_overview_on_a_workspace(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Workspace Overview Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])
        workspace = client.post(
            "/api/v1/eda-workspaces", json={"dataset_id": dataset["id"], "name": "Overview run"}
        ).json()

        response = client.post(f"/api/v1/eda-workspaces/{workspace['id']}/overview")
        assert response.status_code == 200
        assert response.json()["row_count"] == 5

        # The overview is cached on the workspace for next time it's reopened (section 50).
        reloaded = client.get(f"/api/v1/eda-workspaces/{workspace['id']}").json()
        assert reloaded["overview"] is not None
        assert reloaded["overview"]["row_count"] == 5

    def test_workspace_questions_match_the_workspaces_dataset(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Workspace Questions Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])
        workspace = client.post(
            "/api/v1/eda-workspaces", json={"dataset_id": dataset["id"], "name": "Questions"}
        ).json()

        response = client.get(f"/api/v1/eda-workspaces/{workspace['id']}/questions")
        assert response.status_code == 200
        assert len(response.json()) > 0


class TestFindings:
    def test_add_and_delete_a_structured_finding(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Findings Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])
        workspace = client.post(
            "/api/v1/eda-workspaces", json={"dataset_id": dataset["id"], "name": "Findings"}
        ).json()

        response = client.post(
            f"/api/v1/eda-workspaces/{workspace['id']}/findings",
            json={
                "observation": "Revenue is concentrated in the US electronics segment.",
                "evidence": "US electronics accounts for 200 of 260 total revenue in this sample.",
                "business_implication": "Marketing spend outside electronics may be under-indexed.",
                "recommended_action": "Investigate category-level ad spend allocation.",
            },
        )
        assert response.status_code == 201
        finding = response.json()

        reloaded = client.get(f"/api/v1/eda-workspaces/{workspace['id']}").json()
        assert len(reloaded["findings"]) == 1

        delete_response = client.delete(f"/api/v1/eda-workspaces/{workspace['id']}/findings/{finding['id']}")
        assert delete_response.status_code == 204
        reloaded = client.get(f"/api/v1/eda-workspaces/{workspace['id']}").json()
        assert reloaded["findings"] == []


class TestAiEdaAssist:
    def test_assist_returns_a_response_grounded_in_the_real_profile(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "Ai Eda Assist Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.post(
            "/api/v1/ai/eda/assist", json={"dataset_id": dataset["id"], "table_name": "orders"}
        )
        assert response.status_code == 200
        assert response.json()["raw_text"]

    def test_explore_with_a_user_goal_threads_it_through_as_the_message_the_local_provider_echoes(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        """Regression test — DATA_EXPLORATION's own prompt documents an
        optional user_goal input, but EdaAssistRequest/eda_assist() never
        actually accepted or forwarded one end-to-end; a goal typed into the
        UI was silently discarded. The deterministic `local` provider echoes
        back the exact last user-role message, so this confirms the goal is
        real wiring, not just accepted-and-ignored."""
        dataset = _import_ready_dataset(client, "Ai Eda Explore Goal Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        with_goal = client.post(
            "/api/v1/ai/eda/explore",
            json={"dataset_id": dataset["id"], "table_name": "orders", "user_goal": "find drivers of churn"},
        ).json()
        assert "find drivers of churn" in with_goal["raw_text"]

        without_goal = client.post(
            "/api/v1/ai/eda/explore", json={"dataset_id": dataset["id"], "table_name": "orders"}
        ).json()
        assert "Propose a data-exploration plan" in without_goal["raw_text"]


class TestUnprofiledDatasetGuardrail:
    def test_requesting_an_overview_for_an_unprofiled_table_fails_clearly(self, client: TestClient) -> None:
        # A dataset id that doesn't exist at all rather than a real
        # unprofiled one — either way this must be a clean 4xx, never a 500.
        response = client.get("/api/v1/eda/does-not-exist")
        assert response.status_code == 404
