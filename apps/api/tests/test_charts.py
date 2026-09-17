"""Integration tests for saved charts + chart data/recommendation/mistake
detection (sections 22-27 of the Phase 5 spec)."""

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
        ["US", 120.0],
        ["US", 80.0],
        ["UK", 20.0],
        ["UK", 25.0],
        ["FR", 15.0],
    ]
    content = _csv_bytes(["country", "revenue"], rows)
    client.post(
        "/api/v1/datasets/import", files=[("files", ("sales.csv", content, "text/csv"))], data={"name": name}
    )
    return client.get(f"/api/v1/datasets/{slug}").json()


class TestChartCrud:
    def test_create_get_update_delete_a_chart(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "chart-crud-dataset", "Chart Crud Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        created = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "sales",
                "chart_type": "bar",
                "title": "Revenue by country",
                "config": {"x": "country", "y": "revenue", "aggregation": "SUM"},
            },
        )
        assert created.status_code == 201
        chart = created.json()
        assert chart["title"] == "Revenue by country"
        assert chart["config"]["x"] == "country"

        fetched = client.get(f"/api/v1/charts/{chart['id']}")
        assert fetched.status_code == 200

        listed = client.get("/api/v1/charts", params={"dataset_id": dataset["id"]}).json()
        assert any(c["id"] == chart["id"] for c in listed)

        updated = client.patch(f"/api/v1/charts/{chart['id']}", json={"title": "Renamed chart"}).json()
        assert updated["title"] == "Renamed chart"

        delete_response = client.delete(f"/api/v1/charts/{chart['id']}")
        assert delete_response.status_code == 204
        assert client.get(f"/api/v1/charts/{chart['id']}").status_code == 404

    def test_creating_a_chart_against_an_unknown_table_fails_clearly(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "chart-bad-table-dataset", "Chart Bad Table Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        response = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "does_not_exist",
                "chart_type": "bar",
                "title": "x",
                "config": {"x": "country"},
            },
        )
        assert response.status_code == 404


class TestChartData:
    def test_bar_chart_data_reflects_real_aggregated_query_results(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "chart-data-dataset", "Chart Data Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        chart = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "sales",
                "chart_type": "bar",
                "title": "Revenue by country",
                "config": {"x": "country", "y": "revenue", "aggregation": "SUM", "sort": "y_desc"},
            },
        ).json()

        data = client.get(f"/api/v1/charts/{chart['id']}/data").json()
        by_country = dict(zip(data["x_values"], data["series"][0]["y_values"], strict=True))
        assert by_country["US"] == 200.0
        assert by_country["UK"] == 45.0
        assert by_country["FR"] == 15.0

    def test_referencing_an_unknown_column_fails_clearly(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "chart-unknown-col-dataset", "Chart Unknown Col Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        chart = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "sales",
                "chart_type": "bar",
                "title": "Bad column",
                "config": {"x": "not_a_real_column"},
            },
        ).json()

        response = client.get(f"/api/v1/charts/{chart['id']}/data")
        assert response.status_code == 400


class TestMistakeWarningsOnRealCharts:
    def test_a_pie_chart_with_too_many_categories_is_flagged(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        rows = [[f"category_{i}", i] for i in range(12)]
        content = _csv_bytes(["category", "value"], rows)
        client.post(
            "/api/v1/datasets/import",
            files=[("files", ("cats.csv", content, "text/csv"))],
            data={"name": "Many Categories Dataset"},
        )
        dataset = client.get("/api/v1/datasets/many-categories-dataset").json()
        dataset_dirs_cleanup.append(dataset["slug"])

        chart = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "cats",
                "chart_type": "pie",
                "title": "Too many slices",
                "config": {"x": "category", "y": "value", "aggregation": "SUM"},
            },
        ).json()

        data = client.get(f"/api/v1/charts/{chart['id']}/data").json()
        assert any("slices" in w for w in data["warnings"])

    def test_a_well_labeled_sorted_bar_chart_has_no_warnings(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "clean-chart-dataset", "Clean Chart Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        chart = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "sales",
                "chart_type": "bar",
                "title": "Revenue by country",
                "config": {
                    "x": "country",
                    "y": "revenue",
                    "aggregation": "SUM",
                    "sort": "y_desc",
                    "x_label": "Country",
                    "y_label": "Revenue",
                },
            },
        ).json()

        data = client.get(f"/api/v1/charts/{chart['id']}/data").json()
        assert data["warnings"] == []


class TestRecommendation:
    def test_recommend_endpoint_matches_the_deterministic_engine(self, client: TestClient) -> None:
        response = client.post("/api/v1/charts/recommend", json={"x_type": "datetime", "y_type": "numeric"})
        assert response.status_code == 200
        assert response.json()["chart_type"] == "line"

    def test_chart_data_surfaces_a_recommendation_when_the_chosen_type_differs(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        dataset = _import_ready_dataset(client, "recommend-dataset", "Recommend Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        # Deliberately request a scatter plot for a categorical x numeric pair,
        # where the engine would recommend a bar chart instead.
        chart = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "sales",
                "chart_type": "scatter",
                "title": "Mismatched chart type",
                "config": {"x": "country", "y": "revenue"},
            },
        ).json()
        data = client.get(f"/api/v1/charts/{chart['id']}/data").json()
        assert data["recommendation"] is not None
        assert "bar" in data["recommendation"]


class TestInsights:
    def test_add_insight_fields_to_a_chart(self, client: TestClient, dataset_dirs_cleanup: list[str]) -> None:
        dataset = _import_ready_dataset(client, "insight-dataset", "Insight Dataset")
        dataset_dirs_cleanup.append(dataset["slug"])

        chart = client.post(
            "/api/v1/charts",
            json={
                "dataset_id": dataset["id"],
                "table_name": "sales",
                "chart_type": "bar",
                "title": "Revenue by country",
                "config": {"x": "country", "y": "revenue", "aggregation": "SUM"},
            },
        ).json()

        updated = client.patch(
            f"/api/v1/charts/{chart['id']}",
            json={
                "insight_observation": "US drives most revenue.",
                "insight_why_it_matters": "Concentration risk in a single market.",
                "insight_recommended_action": "Diversify acquisition spend to UK/FR.",
            },
        ).json()
        assert updated["insight_observation"] == "US drives most revenue."
        assert updated["insight_recommended_action"] == "Diversify acquisition spend to UK/FR."
