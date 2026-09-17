"""File-format conversion, validation, and fingerprinting for dataset import
(sections 5/39/41/48 of the Phase 5 spec).

CSV/Parquet/JSON go through DuckDB directly (already a core dependency —
section 42: "avoid loading entire datasets into Python when unnecessary").
XLSX is the one format DuckDB can't read natively here, so it's read with
openpyxl (a lightweight, pure-Python core dependency — see pyproject.toml)
one sheet at a time, staged to CSV, then handed to the same DuckDB path —
every format converges on the same "canonical Parquet" step.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import duckdb

from app.core.errors import AppError

_READ_FUNCTION_BY_FORMAT = {"csv": "read_csv_auto", "parquet": "read_parquet", "json": "read_json_auto"}
_CHUNK_SIZE = 1024 * 1024


def compute_fingerprint(paths: list[Path]) -> str:
    """A stable sha256 over one or more files' contents (order-independent —
    sorted by path — so re-uploading the same files in a different order
    doesn't register as a change). Streamed in chunks; never loads a whole
    file into memory (section 47)."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.name):
        digest.update(path.name.encode("utf-8"))
        with path.open("rb") as f:
            while chunk := f.read(_CHUNK_SIZE):
                digest.update(chunk)
    return digest.hexdigest()


def xlsx_sheet_names(path: Path) -> list[str]:
    import openpyxl

    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 — any parse failure means "not a valid xlsx"
        raise AppError(f"'{path.name}' could not be read as an Excel file: {exc}") from exc
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()


def xlsx_sheet_to_csv(path: Path, sheet_name: str, dest_csv: Path) -> None:
    """Streams one sheet's rows to CSV — read_only mode means openpyxl never
    holds the whole worksheet in memory at once (section 47)."""
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = wb[sheet_name]
        with dest_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            wrote_header = False
            for row in sheet.iter_rows(values_only=True):
                if not wrote_header and all(v is None for v in row):
                    continue  # skip a fully-blank leading row rather than emitting it as the header
                writer.writerow(["" if v is None else v for v in row])
                wrote_header = True
    finally:
        wb.close()


def validate_readable(path: Path, file_format: str) -> None:
    """Confirms the file actually parses as its declared format before it's
    registered — catches a corrupted download, a mislabeled extension, or a
    truncated upload with an actionable message (section 48)."""
    if file_format == "xlsx":
        xlsx_sheet_names(path)  # raises AppError on failure
        return
    read_fn = _READ_FUNCTION_BY_FORMAT.get(file_format)
    if read_fn is None:
        raise AppError(f"Unsupported file format '{file_format}'.")
    con = duckdb.connect(":memory:")
    try:
        con.execute(f"SELECT * FROM {read_fn}('{path.as_posix()}') LIMIT 1").fetchall()
    except duckdb.Error as exc:
        raise AppError(
            f"'{path.name}' could not be parsed as {file_format.upper()}: {exc}",
            details={"filename": path.name, "file_format": file_format},
        ) from exc
    finally:
        con.close()


def convert_to_parquet(src_path: Path, file_format: str, dest_parquet: Path) -> None:
    """Writes the canonical Parquet copy DuckDB/SQL Lab/Python Lab actually
    query (section 41: "Use Parquet as the preferred internal analytical
    format"). `file_format` must be csv/parquet/json — route XLSX through
    `xlsx_sheet_to_csv` first."""
    read_fn = _READ_FUNCTION_BY_FORMAT.get(file_format)
    if read_fn is None:
        raise AppError(f"Unsupported file format '{file_format}'.")
    con = duckdb.connect(":memory:")
    try:
        con.execute(
            f"COPY (SELECT * FROM {read_fn}('{src_path.as_posix()}')) "
            f"TO '{dest_parquet.as_posix()}' (FORMAT PARQUET)"
        )
    except duckdb.Error as exc:
        raise AppError(f"'{src_path.name}' could not be converted: {exc}") from exc
    finally:
        con.close()


def introspect(path: Path, file_format: str = "parquet") -> tuple[int, int]:
    """Returns (row_count, column_count) for an already-canonical file."""
    read_fn = _READ_FUNCTION_BY_FORMAT[file_format]
    con = duckdb.connect(":memory:")
    try:
        con.execute(f"CREATE VIEW t AS SELECT * FROM {read_fn}('{path.as_posix()}')")
        row_count = con.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        column_count = len(con.execute("DESCRIBE t").fetchall())
        return row_count, column_count
    finally:
        con.close()
