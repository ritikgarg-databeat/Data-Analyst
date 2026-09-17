"""Cross-subsystem integration tests (section 57 "Integration" + sections
32-34 of the Phase 5 spec): Dataset -> SQL Lab, Dataset -> Python Lab, and
Dataset -> Project shell — proving a Phase 5 import is immediately usable
by Phase 3/4 features with zero changes to either, plus the
correlation/distribution/time-series explorer endpoints."""

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


def _import_ready_dataset(client: TestClient, slug: str, name: str) -> dict:
    rows = [
        ["2024-01-05", "US", 100.0, 5],
        ["2024-01-20", "US", 200.0, 10],
        ["2024-02-01", "UK", 50.0, 2],
        ["2024-02-15", "UK", 75.0, 3],
    ]
    content = _csv_bytes(["order_date", "country", "revenue", "quantity"], rows)
    client.post(
        "/api/v1/datasets/import", files=[("files", ("orders.csv", content, "text/csv"))], data={"name": name}
    )
    return client.get(f"/api/v1/datasets/{slug}").json()


class TestDatasetToSqlLab:
    def test_an_imported_dataset_is_immediately_queryable_in_the_sql_lab(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "sql-integration-dataset", "Sql Integration Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        databases = client.get("/api/v1/sql/databases").json()
        assert any(d["name"] == dataset["slug"] for d in databases)

        tables = client.get(f"/api/v1/sql/databases/{dataset['slug']}/tables").json()
        assert any(t["table_name"] == "orders" for t in tables)

        response = client.post(
            "/api/v1/sql/execute",
            json={
                "engine": "duckdb",
                "database": dataset["slug"],
                "query": "SELECT COUNT(*) AS n FROM orders;",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["rows"][0][0] == 4

    def test_a_multi_table_collection_is_fully_joinable_in_the_sql_lab(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        customers = _csv_bytes(["customer_id", "name"], [[1, "Ann"], [2, "Bob"]])
        orders = _csv_bytes(["order_id", "customer_id", "revenue"], [[1, 1, 100], [2, 2, 50], [3, 1, 25]])
        client.post(
            "/api/v1/datasets/import",
            files=[
                ("files", ("customers.csv", customers, "text/csv")),
                ("files", ("orders.csv", orders, "text/csv")),
            ],
            data={"name": "Sql Join Collection"},
        )
        dataset = client.get("/api/v1/datasets/sql-join-collection").json()
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.post(
            "/api/v1/sql/execute",
            json={
                "engine": "duckdb",
                "database": dataset["slug"],
                "query": (
                    "SELECT c.name, SUM(o.revenue) AS total "
                    "FROM orders o JOIN customers c ON o.customer_id = c.customer_id "
                    "GROUP BY c.name ORDER BY c.name;"
                ),
            },
        )
        assert response.status_code == 200
        rows = {r[0]: r[1] for r in response.json()["rows"]}
        assert rows["Ann"] == 125
        assert rows["Bob"] == 50


class TestDatasetToPythonLab:
    def test_an_imported_dataset_is_listed_for_the_python_lab_with_a_valid_container_path(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "python-integration-dataset", "Python Integration Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        files = client.get("/api/v1/python/datasets").json()
        matches = [f for f in files if f["dataset_slug"] == dataset["slug"]]
        assert len(matches) == 1
        entry = matches[0]
        assert entry["container_path"] == f"/data/datasets/{dataset['slug']}/orders.parquet"
        assert "pd.read_parquet(" in entry["suggested_code"]
        assert entry["row_count"] == 4


class TestDatasetToProjectShell:
    def test_create_project_from_dataset_produces_a_shell_referencing_it(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "project-shell-dataset", "Project Shell Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.post(
            f"/api/v1/projects/from-dataset/{dataset['id']}",
            json={"name": "My analysis project"},
        )
        assert response.status_code == 201
        project = response.json()
        assert project["dataset_id"] == dataset["id"]
        assert project["name"] == "My analysis project"
        assert project["status"] == "NOT_STARTED"  # Phase 8: Project.status is now CaseAttemptStatus

        listed = client.get("/api/v1/projects").json()
        assert any(p["id"] == project["id"] for p in listed)

    def test_project_notes_and_status_can_be_updated(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "project-update-dataset", "Project Update Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])
        project = client.post(f"/api/v1/projects/from-dataset/{dataset['id']}", json={}).json()

        updated = client.patch(
            f"/api/v1/projects/{project['id']}",
            json={"notes": "Found a strong US/UK split.", "status": "IN_PROGRESS"},
        ).json()
        assert updated["notes"] == "Found a strong US/UK split."
        assert updated["status"] == "IN_PROGRESS"


class TestAnalysisExplorers:
    def test_correlation_endpoint(self, client: TestClient, dataset_dirs_cleanup: list[str]) -> None:
        dataset = _import_ready_dataset(
            client, "correlation-endpoint-dataset", "Correlation Endpoint Dataset"
        )
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.get(
            f"/api/v1/datasets/{dataset['slug']}/analysis/correlation",
            params={"columns": "revenue,quantity", "method": "pearson"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["columns"] == ["revenue", "quantity"]
        assert body["matrix"][0][0] == 1.0
        assert "does not imply causation" in body["note"]

    def test_distribution_endpoint(self, client: TestClient, dataset_dirs_cleanup: list[str]) -> None:
        dataset = _import_ready_dataset(
            client, "distribution-endpoint-dataset", "Distribution Endpoint Dataset"
        )
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.get(
            f"/api/v1/datasets/{dataset['slug']}/analysis/distribution",
            params={"column": "revenue", "bins": 4},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["bins"]) == 4
        assert body["mean"] is not None

    def test_time_series_endpoint(self, client: TestClient, dataset_dirs_cleanup: list[str]) -> None:
        dataset = _import_ready_dataset(client, "timeseries-endpoint-dataset", "Timeseries Endpoint Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.get(
            f"/api/v1/datasets/{dataset['slug']}/analysis/timeseries",
            params={
                "date_column": "order_date",
                "metric_column": "revenue",
                "aggregation": "SUM",
                "granularity": "month",
            },
        )
        assert response.status_code == 200
        points = response.json()["points"]
        assert len(points) == 2  # January and February
        assert points[0]["value"] == 300.0
        assert points[1]["value"] == 125.0

    def test_duplicates_and_outliers_endpoints(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _csv_bytes(["value"], [[v] for v in [1, 2, 3, 3, 1000]])
        client.post(
            "/api/v1/datasets/import",
            files=[("files", ("dup.csv", content, "text/csv"))],
            data={"name": "Dup Outlier Dataset"},
        )
        dataset = client.get("/api/v1/datasets/dup-outlier-dataset").json()
        dataset_dirs_cleanup.append(dataset["slug"])

        duplicates = client.get(f"/api/v1/datasets/{dataset['slug']}/duplicates").json()
        assert duplicates["duplicate_row_count"] == 1

        outliers = client.get(
            f"/api/v1/datasets/{dataset['slug']}/outliers", params={"column": "value"}
        ).json()
        assert outliers["outlier_count"] == 1
