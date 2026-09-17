"""Unit tests for app/dataset_hub/converters.py — fingerprinting, format
validation, and CSV/JSON/XLSX-to-Parquet conversion (sections 39/41/48 of
the Phase 5 spec)."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from app.core.errors import AppError
from app.dataset_hub.converters import (
    compute_fingerprint,
    convert_to_parquet,
    introspect,
    validate_readable,
    xlsx_sheet_names,
    xlsx_sheet_to_csv,
)


def _write_csv(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")


class TestFingerprint:
    def test_identical_content_under_different_filenames_still_differs(self, tmp_path: Path) -> None:
        a = tmp_path / "a.csv"
        b = tmp_path / "b.csv"
        _write_csv(a, "x,y\n1,2\n")
        _write_csv(b, "x,y\n1,2\n")
        assert compute_fingerprint([a]) != compute_fingerprint([b])  # the filename is part of the fingerprint

    def test_identical_file_reimported_produces_the_same_fingerprint(self, tmp_path: Path) -> None:
        a = tmp_path / "a.csv"
        _write_csv(a, "x,y\n1,2\n")
        assert compute_fingerprint([a]) == compute_fingerprint([a])

    def test_changed_content_changes_the_fingerprint(self, tmp_path: Path) -> None:
        a = tmp_path / "a.csv"
        _write_csv(a, "x,y\n1,2\n")
        fp1 = compute_fingerprint([a])
        _write_csv(a, "x,y\n1,3\n")
        fp2 = compute_fingerprint([a])
        assert fp1 != fp2

    def test_file_order_does_not_change_a_multi_file_fingerprint(self, tmp_path: Path) -> None:
        a, b = tmp_path / "a.csv", tmp_path / "b.csv"
        _write_csv(a, "1")
        _write_csv(b, "2")
        assert compute_fingerprint([a, b]) == compute_fingerprint([b, a])


class TestValidateReadable:
    def test_a_well_formed_csv_passes(self, tmp_path: Path) -> None:
        path = tmp_path / "ok.csv"
        _write_csv(path, "a,b\n1,2\n")
        validate_readable(path, "csv")  # does not raise

    def test_a_corrupted_parquet_file_is_rejected_with_an_actionable_message(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.parquet"
        path.write_bytes(b"this is not a real parquet file")
        with pytest.raises(AppError, match="could not be parsed"):
            validate_readable(path, "parquet")

    def test_malformed_json_is_rejected(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(AppError):
            validate_readable(path, "json")


class TestConvertToParquet:
    def test_csv_converts_to_a_queryable_parquet_file(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "src.csv"
        _write_csv(csv_path, "a,b\n1,x\n2,y\n3,z\n")
        parquet_path = tmp_path / "out.parquet"
        convert_to_parquet(csv_path, "csv", parquet_path)
        assert parquet_path.exists()
        row_count, column_count = introspect(parquet_path)
        assert row_count == 3
        assert column_count == 2

    def test_json_converts_to_parquet(self, tmp_path: Path) -> None:
        json_path = tmp_path / "src.json"
        json_path.write_text('[{"a": 1}, {"a": 2}]', encoding="utf-8")
        parquet_path = tmp_path / "out.parquet"
        convert_to_parquet(json_path, "json", parquet_path)
        row_count, _ = introspect(parquet_path)
        assert row_count == 2


class TestXlsx:
    def _make_workbook(self, path: Path, sheets: dict[str, list[list]]) -> None:
        import openpyxl

        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for name, rows in sheets.items():
            ws = wb.create_sheet(name)
            for row in rows:
                ws.append(row)
        wb.save(path)

    def test_lists_sheet_names(self, tmp_path: Path) -> None:
        path = tmp_path / "book.xlsx"
        self._make_workbook(path, {"Customers": [["id", "name"], [1, "Ann"]], "Orders": [["id"], [1]]})
        assert xlsx_sheet_names(path) == ["Customers", "Orders"]

    def test_sheet_exports_to_a_readable_csv(self, tmp_path: Path) -> None:
        path = tmp_path / "book.xlsx"
        self._make_workbook(path, {"Sheet1": [["id", "name"], [1, "Ann"], [2, "Bob"]]})
        csv_path = tmp_path / "sheet1.csv"
        xlsx_sheet_to_csv(path, "Sheet1", csv_path)
        con = duckdb.connect(":memory:")
        rows = con.execute(f"SELECT * FROM read_csv_auto('{csv_path.as_posix()}')").fetchall()
        con.close()
        assert len(rows) == 2

    def test_an_invalid_xlsx_file_raises_a_clear_error(self, tmp_path: Path) -> None:
        path = tmp_path / "fake.xlsx"
        path.write_bytes(b"not a real xlsx file")
        with pytest.raises(AppError):
            xlsx_sheet_names(path)
