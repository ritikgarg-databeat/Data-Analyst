"""Integration tests for the Dataset Hub's local import pipeline, run
through the real HTTP stack (client fixture) — covers sections 5-18, 39-41
of the Phase 5 spec: CSV/Parquet/JSON/XLSX import, folder/collection
import, schema/profile/quality/duplicates/outliers, versioning/fingerprint,
relationships, notes, and usage. Background import runs synchronously
under TestClient (see app/services/dataset_service.py's module docstring),
so no polling is needed — the POST response already reflects the finished
import."""

from __future__ import annotations

import csv
import io
import json

import duckdb
from fastapi.testclient import TestClient


def _csv_bytes(headers: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _xlsx_bytes(sheets: dict[str, list[list]]) -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _import(client: TestClient, files: list[tuple], data: dict) -> dict:
    """POSTs /datasets/import, then re-fetches the dataset by slug.

    The POST response body is a snapshot taken the instant the endpoint
    returns — *before* the `BackgroundTasks` entry it just registered has
    run (that's the whole point of returning immediately with IMPORTING,
    section 4/46 of the spec — the frontend polls GET .../{slug} for
    progress). TestClient happens to run the background task synchronously
    within this same `client.post()` call, so by the time control returns
    here the import has already finished — a follow-up GET (not the POST
    response itself) is what reflects that finished state."""
    created = client.post("/api/v1/datasets/import", files=files, data=data).json()
    return client.get(f"/api/v1/datasets/{created['slug']}").json()


def _reimport(client: TestClient, slug: str, files: list[tuple]) -> dict:
    client.post(f"/api/v1/datasets/{slug}/reimport", files=files)
    return client.get(f"/api/v1/datasets/{slug}").json()


def _parquet_bytes(headers: list[str], rows: list[list]) -> bytes:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        csv_path = Path(tmp) / "src.csv"
        csv_path.write_bytes(_csv_bytes(headers, rows))
        parquet_path = Path(tmp) / "src.parquet"
        con = duckdb.connect(":memory:")
        con.execute(
            f"COPY (SELECT * FROM read_csv_auto('{csv_path.as_posix()}')) TO "
            f"'{parquet_path.as_posix()}' (FORMAT PARQUET)"
        )
        con.close()
        return parquet_path.read_bytes()


class TestCsvImport:
    def test_import_a_single_csv_ends_ready_with_correct_counts(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        rows = [[1, 100.0, "US"], [2, 50.0, "UK"], [3, 75.0, "US"]]
        content = _csv_bytes(["order_id", "revenue", "country"], rows)
        body = _import(
            client,
            [("files", ("orders.csv", content, "text/csv"))],
            {"name": "Test CSV Import", "business_domain": "E-commerce", "tags": "e-commerce,beginner"},
        )
        dataset_dirs_cleanup.append(body["slug"])
        assert body["status"] == "READY"
        assert body["row_count"] == 3
        assert body["column_count"] == 3
        assert body["source_type"] == "LOCAL"
        assert body["business_domain"] == "E-commerce"
        assert set(body["tags"]) == {"e-commerce", "beginner"}
        assert body["fingerprint"] is not None
        assert body["version"] == 1
        assert len(body["tables"]) == 1
        assert body["sql_ready"] is True
        assert body["python_ready"] is True

    def test_schema_endpoint_reflects_the_imported_columns(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _csv_bytes(["a", "b"], [[1, "x"], [2, None], [3, "y"]])
        created = _import(client, [("files", ("cols.csv", content, "text/csv"))], {"name": "Schema Test"})
        dataset_dirs_cleanup.append(created["slug"])

        response = client.get(f"/api/v1/datasets/{created['slug']}/schema")
        assert response.status_code == 200
        [table_schema] = response.json()
        names = {c["column_name"] for c in table_schema["columns"]}
        assert names == {"a", "b"}

    def test_profile_and_quality_endpoints_return_real_computed_stats(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _csv_bytes(["value"], [[v] for v in [10, 20, 30, 40, 1000]])
        created = _import(client, [("files", ("nums.csv", content, "text/csv"))], {"name": "Profile Test"})
        dataset_dirs_cleanup.append(created["slug"])

        profile = client.get(f"/api/v1/datasets/{created['slug']}/profile").json()
        col = profile["tables"][0]["columns"][0]
        assert col["outlier_count"] == 1

        quality = client.get(f"/api/v1/datasets/{created['slug']}/quality").json()
        report = quality["tables"][0]
        assert 0 <= report["overall_score"] <= 100
        assert "weighted average" in report["methodology"]


class TestParquetImport:
    def test_import_a_parquet_file(self, client: TestClient, dataset_dirs_cleanup: list[str]) -> None:
        content = _parquet_bytes(["a", "b"], [[1, "x"], [2, "y"]])
        body = _import(
            client,
            [("files", ("data.parquet", content, "application/octet-stream"))],
            {"name": "Parquet Import"},
        )
        dataset_dirs_cleanup.append(body["slug"])
        assert body["status"] == "READY"
        assert body["row_count"] == 2


class TestJsonImport:
    def test_import_a_json_array_of_records(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = json.dumps([{"id": 1, "name": "Ann"}, {"id": 2, "name": "Bob"}]).encode("utf-8")
        body = _import(
            client, [("files", ("people.json", content, "application/json"))], {"name": "JSON Import"}
        )
        dataset_dirs_cleanup.append(body["slug"])
        assert body["status"] == "READY"
        assert body["row_count"] == 2


_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class TestXlsxImport:
    def test_import_a_single_sheet_workbook(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _xlsx_bytes({"Sheet1": [["id", "name"], [1, "Ann"], [2, "Bob"], [3, "Cid"]]})
        body = _import(
            client,
            [("files", ("book.xlsx", content, _XLSX_MIME))],
            {"name": "Xlsx Import"},
        )
        dataset_dirs_cleanup.append(body["slug"])
        assert body["status"] == "READY"
        assert body["row_count"] == 3

    def test_multi_sheet_workbook_becomes_a_multi_table_collection(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _xlsx_bytes(
            {
                "Customers": [["id", "name"], [1, "Ann"]],
                "Orders": [["id", "customer_id"], [1, 1], [2, 1]],
            }
        )
        body = _import(
            client,
            [("files", ("multi.xlsx", content, _XLSX_MIME))],
            {"name": "Xlsx Collection"},
        )
        dataset_dirs_cleanup.append(body["slug"])
        assert body["status"] == "READY"
        assert len(body["tables"]) == 2
        table_names = {t["table_name"] for t in body["tables"]}
        assert any("customers" in n for n in table_names)
        assert any("orders" in n for n in table_names)


class TestFolderCollectionImport:
    def test_multiple_files_in_one_request_become_one_dataset_collection(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        customers = _csv_bytes(["customer_id", "name"], [[1, "Ann"], [2, "Bob"]])
        orders = _csv_bytes(["order_id", "customer_id"], [[1, 1], [2, 1], [3, 2]])
        body = _import(
            client,
            [
                ("files", ("customers.csv", customers, "text/csv")),
                ("files", ("orders.csv", orders, "text/csv")),
            ],
            {"name": "Mini Ecommerce Collection"},
        )
        dataset_dirs_cleanup.append(body["slug"])
        assert body["status"] == "READY"
        assert len(body["tables"]) == 2
        assert body["row_count"] == 5  # 2 customers + 3 orders, summed
        table_names = {t["table_name"] for t in body["tables"]}
        assert table_names == {"customers", "orders"}

    def test_filenames_that_slugify_to_the_same_table_name_are_deduplicated_not_overwritten(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        """Regression test: "Sales Report.csv" and "Sales-Report.csv" both
        slugify to table_name "sales_report" via table_name_from_filename —
        without de-duplication, the second file's conversion silently
        overwrote the first file's Parquet output on disk, and two
        DatasetTable rows were created with the identical table_name (the
        first one describing stale metadata for what was actually the
        second file's data)."""
        first = _csv_bytes(["id", "amount"], [[1, 100], [2, 200]])
        second = _csv_bytes(["id", "region", "amount"], [[1, "west", 10], [2, "east", 20], [3, "west", 30]])
        body = _import(
            client,
            [
                ("files", ("Sales Report.csv", first, "text/csv")),
                ("files", ("Sales-Report.csv", second, "text/csv")),
            ],
            {"name": "Collision Collection"},
        )
        dataset_dirs_cleanup.append(body["slug"])

        assert body["status"] == "READY"
        assert len(body["tables"]) == 2
        table_names = {t["table_name"] for t in body["tables"]}
        assert len(table_names) == 2  # never collapses to one via a silent overwrite
        assert "sales_report" in table_names
        row_counts = sorted(t["row_count"] for t in body["tables"])
        assert row_counts == [2, 3]  # both files' real row counts survive, neither is lost/overwritten

    def test_relationships_can_be_declared_between_collection_tables(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        customers = _csv_bytes(["customer_id", "name"], [[1, "Ann"]])
        orders = _csv_bytes(["order_id", "customer_id"], [[1, 1]])
        created = _import(
            client,
            [
                ("files", ("customers.csv", customers, "text/csv")),
                ("files", ("orders.csv", orders, "text/csv")),
            ],
            {"name": "Relationship Collection"},
        )
        dataset_dirs_cleanup.append(created["slug"])

        response = client.post(
            f"/api/v1/datasets/{created['slug']}/relationships",
            json={
                "from_table": "orders",
                "from_column": "customer_id",
                "to_table": "customers",
                "to_column": "customer_id",
                "relationship_type": "many_to_one",
            },
        )
        assert response.status_code == 201
        listed = client.get(f"/api/v1/datasets/{created['slug']}/relationships").json()
        assert len(listed) == 1
        assert listed[0]["from_table"] == "orders"


class TestVersioningAndFingerprint:
    def test_reimporting_changed_data_bumps_the_version(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        v1 = _csv_bytes(["a"], [[1], [2]])
        created = _import(client, [("files", ("v.csv", v1, "text/csv"))], {"name": "Versioned Dataset"})
        dataset_dirs_cleanup.append(created["slug"])
        assert created["version"] == 1
        fingerprint_v1 = created["fingerprint"]

        v2 = _csv_bytes(["a"], [[1], [2], [3], [4]])
        reimported = _reimport(client, created["slug"], [("files", ("v.csv", v2, "text/csv"))])
        assert reimported["version"] == 2
        assert reimported["fingerprint"] != fingerprint_v1
        assert reimported["row_count"] == 4

        versions = client.get(f"/api/v1/datasets/{created['slug']}/versions").json()
        assert len(versions) == 2
        assert {v["version"] for v in versions} == {1, 2}

    def test_reimporting_identical_data_does_not_bump_the_version(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _csv_bytes(["a"], [[1], [2]])
        created = _import(client, [("files", ("same.csv", content, "text/csv"))], {"name": "Stable Dataset"})
        dataset_dirs_cleanup.append(created["slug"])

        reimported = _reimport(client, created["slug"], [("files", ("same.csv", content, "text/csv"))])
        assert reimported["version"] == 1


class TestNotesAndUsage:
    def test_add_and_list_notes_at_dataset_and_column_level(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _csv_bytes(["revenue"], [[100], [200]])
        created = _import(client, [("files", ("notes.csv", content, "text/csv"))], {"name": "Notes Dataset"})
        dataset_dirs_cleanup.append(created["slug"])

        client.post(f"/api/v1/datasets/{created['slug']}/notes", json={"body": "Dataset-level note"})
        client.post(
            f"/api/v1/datasets/{created['slug']}/notes",
            json={"body": "Revenue looks skewed.", "column_name": "revenue"},
        )
        notes = client.get(f"/api/v1/datasets/{created['slug']}/notes").json()
        assert len(notes) == 2

    def test_usage_endpoint_reports_zero_for_a_brand_new_dataset(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        content = _csv_bytes(["a"], [[1]])
        created = _import(client, [("files", ("fresh.csv", content, "text/csv"))], {"name": "Fresh Dataset"})
        dataset_dirs_cleanup.append(created["slug"])

        usage = client.get(f"/api/v1/datasets/{created['slug']}/usage").json()
        assert usage == {
            "sql_exercises": 0,
            "python_exercises": 0,
            "other_exercises": 0,
            "eda_workspaces": 0,
            "charts": 0,
            "projects": 0,
        }


class TestValidationErrors:
    def test_unsupported_file_extension_is_rejected_with_a_clear_error(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/datasets/import",
            files=[("files", ("script.exe", b"MZ\x90\x00", "application/octet-stream"))],
            data={"name": "Bad Extension"},
        )
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["error"]["message"]

    def test_empty_file_is_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/datasets/import",
            files=[("files", ("empty.csv", b"", "text/csv"))],
            data={"name": "Empty File"},
        )
        assert response.status_code == 400

    def test_corrupted_parquet_ends_the_dataset_in_failed_status_not_a_crash(
        self, client: TestClient, dataset_dirs_cleanup: list[str]
    ) -> None:
        body = _import(
            client,
            [("files", ("bad.parquet", b"not a real parquet file at all", "application/octet-stream"))],
            {"name": "Corrupted Parquet"},
        )
        dataset_dirs_cleanup.append(body["slug"])
        assert body["status"] == "FAILED"
        assert body["status_message"]

    def test_getting_an_unknown_dataset_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/datasets/does-not-exist-at-all")
        assert response.status_code == 404
