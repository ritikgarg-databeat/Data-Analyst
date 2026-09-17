"""Import orchestration (sections 5-10, 39-41, 46-48 of the Phase 5 spec) —
runs as a FastAPI `BackgroundTasks` body so the upload/Kaggle-import HTTP
request returns immediately with the Dataset row in IMPORTING status while
this does the actual conversion + profiling work (see the module docstring
of app/services/dataset_service.py for why it's safe to keep reusing the
same request-scoped `db: Session` from inside a background task).
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.errors import AppError
from app.dataset_hub.converters import (
    compute_fingerprint,
    convert_to_parquet,
    introspect,
    validate_readable,
    xlsx_sheet_names,
    xlsx_sheet_to_csv,
)
from app.dataset_hub.paths import datasets_dir_for, processed_dir_for, raw_dir_for, repo_relative
from app.dataset_hub.profiling import profile_table
from app.dataset_hub.quality import score_quality
from app.dataset_hub.security import (
    assert_supported_extension,
    sanitize_filename,
    slugify,
    table_name_from_filename,
)
from app.models.dataset import Dataset, DatasetTable, DatasetVersion
from app.models.dataset_profile import DatasetColumnProfile, DatasetProfile, DatasetQualityReport
from app.models.enums import DatasetStatus
from app.models.sql_lab import SqlTable
from app.sql.paths import resolve_repo_path

logger = logging.getLogger(__name__)

DEFAULT_MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # overridable via Settings.dataset_max_upload_mb
_CHUNK_SIZE = 1024 * 1024


@dataclass
class StagedFile:
    filename: str  # sanitized, e.g. "orders.csv"
    raw_path: Path
    file_format: str  # csv | parquet | json | xlsx


def stage_upload(
    upload: UploadFile, dest_dir: Path, *, max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
) -> StagedFile:
    """Sanitizes the filename and streams the upload to disk in chunks —
    never reads the whole file into memory (section 47), and aborts (with
    the partial file removed) if it exceeds `max_bytes` (section 48)."""
    filename = sanitize_filename(upload.filename or "")
    file_format = assert_supported_extension(filename)
    dest_path = dest_dir / filename

    written = 0
    with dest_path.open("wb") as out:
        while chunk := upload.file.read(_CHUNK_SIZE):
            written += len(chunk)
            if written > max_bytes:
                out.close()
                dest_path.unlink(missing_ok=True)
                raise AppError(
                    f"'{filename}' exceeds the {max_bytes // (1024 * 1024)} MB upload limit.",
                    details={"filename": filename, "max_bytes": max_bytes},
                )
            out.write(chunk)
    if written == 0:
        dest_path.unlink(missing_ok=True)
        raise AppError(f"'{filename}' is empty.")
    return StagedFile(filename=filename, raw_path=dest_path, file_format=file_format)


def stage_uploads(
    files: list[UploadFile], slug: str, *, max_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
) -> list[StagedFile]:
    dest_dir = raw_dir_for(slug)
    staged: list[StagedFile] = []
    try:
        for upload in files:
            if isinstance(upload, StarletteUploadFile) and upload.filename is None:
                continue
            staged.append(stage_upload(upload, dest_dir, max_bytes=max_bytes))
    except Exception:
        for s in staged:
            s.raw_path.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            dest_dir.rmdir()  # only succeeds if now-empty — never removes a dir with other files in it
        raise
    if not staged:
        raise AppError("No files were provided to import.")
    return staged


def _grain_guess(table_name: str) -> str:
    singular = table_name[:-1] if table_name.endswith("s") and len(table_name) > 1 else table_name
    return f"1 row = 1 {singular.replace('_', ' ')}"


@dataclass
class _TableBuild:
    table_name: str
    parquet_path: Path
    row_count: int
    column_count: int
    size_bytes: int


def _dedupe_table_name(table_name: str, used_names: set[str]) -> str:
    """Appends a numeric suffix if `table_name` was already used by an
    earlier file/sheet in this same import — e.g. "Sales Report.csv" and
    "Sales-Report.csv" both slugify to "sales_report" via
    table_name_from_filename, so without this, the second file's conversion
    silently overwrote the first file's Parquet output on disk and created
    a duplicate DatasetTable row carrying the first file's stale
    row/column-count metadata for what was actually the second file's data."""
    if table_name not in used_names:
        used_names.add(table_name)
        return table_name
    suffix = 2
    while f"{table_name}_{suffix}" in used_names:
        suffix += 1
    deduped = f"{table_name}_{suffix}"
    used_names.add(deduped)
    return deduped


def _convert_staged_file(
    staged: StagedFile, processed_dir: Path, datasets_dir: Path, used_names: set[str]
) -> list[_TableBuild]:
    """Converts one staged file to one or more canonical Parquet tables — an
    XLSX workbook with multiple sheets becomes one table per sheet (folded
    into the same "dataset collection" concept as a multi-file folder
    import, section 6). `used_names` is shared and mutated across every
    file/sheet in the same import, so table names never collide within it."""
    builds: list[_TableBuild] = []

    if staged.file_format == "xlsx":
        sheets = xlsx_sheet_names(staged.raw_path)
        if not sheets:
            raise AppError(f"'{staged.filename}' has no sheets.")
        multi = len(sheets) > 1
        stem = Path(staged.filename).stem
        for sheet in sheets:
            csv_path = processed_dir / f"{table_name_from_filename(stem)}_{slugify(sheet)}.csv"
            xlsx_sheet_to_csv(staged.raw_path, sheet, csv_path)
            validate_readable(csv_path, "csv")
            table_name = _dedupe_table_name(
                table_name_from_filename(f"{stem}_{sheet}" if multi else stem), used_names
            )
            parquet_path = datasets_dir / f"{table_name}.parquet"
            convert_to_parquet(csv_path, "csv", parquet_path)
            row_count, column_count = introspect(parquet_path)
            builds.append(
                _TableBuild(table_name, parquet_path, row_count, column_count, parquet_path.stat().st_size)
            )
    else:
        validate_readable(staged.raw_path, staged.file_format)
        table_name = _dedupe_table_name(table_name_from_filename(staged.filename), used_names)
        parquet_path = datasets_dir / f"{table_name}.parquet"
        convert_to_parquet(staged.raw_path, staged.file_format, parquet_path)
        row_count, column_count = introspect(parquet_path)
        builds.append(
            _TableBuild(table_name, parquet_path, row_count, column_count, parquet_path.stat().st_size)
        )

    return builds


def _profile_and_score(db: Session, dataset: Dataset, tables: list[DatasetTable]) -> None:
    for table in tables:
        db.query(DatasetProfile).filter(
            DatasetProfile.dataset_id == dataset.id, DatasetProfile.table_name == table.table_name
        ).delete()
        db.query(DatasetQualityReport).filter(
            DatasetQualityReport.dataset_id == dataset.id, DatasetQualityReport.table_name == table.table_name
        ).delete()
        db.flush()

        table_profile = profile_table(
            resolve_repo_path(table.file_path), "parquet", table.table_name, size_bytes=table.size_bytes
        )
        profile_row = DatasetProfile(
            dataset_id=dataset.id,
            table_name=table.table_name,
            row_count=table_profile.row_count,
            column_count=table_profile.column_count,
            size_bytes=table_profile.size_bytes,
            duplicate_row_count=table_profile.duplicate_row_count,
        )
        db.add(profile_row)
        db.flush()
        for col in table_profile.columns:
            db.add(
                DatasetColumnProfile(
                    profile_id=profile_row.id,
                    column_name=col.column_name,
                    data_type=col.data_type,
                    inferred_sql_type=col.inferred_sql_type,
                    null_count=col.null_count,
                    null_percentage=col.null_percentage,
                    unique_count=col.unique_count,
                    unique_percentage=col.unique_percentage,
                    min_value=col.min_value,
                    max_value=col.max_value,
                    mean=col.mean,
                    median=col.median,
                    std_dev=col.std_dev,
                    quantiles=col.quantiles,
                    zero_count=col.zero_count,
                    negative_count=col.negative_count,
                    outlier_count=col.outlier_count,
                    outlier_method=col.outlier_method,
                    top_values=col.top_values,
                    sample_values=col.sample_values,
                    min_length=col.min_length,
                    max_length=col.max_length,
                    avg_length=col.avg_length,
                    extra=col.extra,
                    display_order=col.display_order,
                )
            )

        quality = score_quality(table_profile)
        db.add(
            DatasetQualityReport(
                dataset_id=dataset.id,
                table_name=table.table_name,
                overall_score=quality.overall_score,
                completeness_score=quality.completeness_score,
                uniqueness_score=quality.uniqueness_score,
                validity_score=quality.validity_score,
                consistency_score=quality.consistency_score,
                duplicate_row_count=quality.duplicate_row_count,
                issues=[
                    {"type": i.type, "detail": i.detail, "severity": i.severity, "column": i.column}
                    for i in quality.issues
                ],
                methodology=quality.methodology,
            )
        )
    dataset.last_profiled_at = datetime.now(UTC)


def process_dataset_import(db: Session, dataset_id: str, staged_files: list[StagedFile]) -> None:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        return

    try:
        dataset.status = DatasetStatus.IMPORTING
        dataset.status_message = None
        db.commit()

        slug = dataset.slug
        datasets_dir = datasets_dir_for(slug)
        processed_dir = processed_dir_for(slug)

        db.query(DatasetTable).filter(DatasetTable.dataset_id == dataset.id).delete()
        db.query(SqlTable).filter(SqlTable.dataset_id == dataset.id).delete()
        db.flush()

        all_builds: list[_TableBuild] = []
        used_table_names: set[str] = set()
        for staged in staged_files:
            all_builds.extend(_convert_staged_file(staged, processed_dir, datasets_dir, used_table_names))

        if not all_builds:
            raise AppError("No tables could be derived from the uploaded file(s).")

        tables: list[DatasetTable] = []
        for order, build in enumerate(all_builds):
            relative_path = repo_relative(build.parquet_path)
            table = DatasetTable(
                dataset_id=dataset.id,
                table_name=build.table_name,
                file_path=relative_path,
                file_format="parquet",
                row_count=build.row_count,
                column_count=build.column_count,
                size_bytes=build.size_bytes,
                grain=_grain_guess(build.table_name),
                display_order=order,
            )
            db.add(table)
            db.add(
                SqlTable(
                    dataset_id=dataset.id,
                    table_name=build.table_name,
                    file_path=relative_path,
                    file_format="parquet",
                    row_count=build.row_count,
                    column_count=build.column_count,
                    grain=_grain_guess(build.table_name),
                    display_order=order,
                )
            )
            tables.append(table)
        db.flush()

        fingerprint = compute_fingerprint([s.raw_path for s in staged_files])
        version_changed = dataset.fingerprint is not None and dataset.fingerprint != fingerprint
        if version_changed:
            dataset.version += 1
        dataset.fingerprint = fingerprint
        dataset.row_count = sum(t.row_count or 0 for t in tables)
        dataset.column_count = sum(t.column_count or 0 for t in tables)
        dataset.size_bytes = sum(t.size_bytes or 0 for t in tables)
        dataset.imported_at = datetime.now(UTC)
        db.add(
            DatasetVersion(
                dataset_id=dataset.id,
                version=dataset.version,
                fingerprint=fingerprint,
                row_count=dataset.row_count,
                column_count=dataset.column_count,
                size_bytes=dataset.size_bytes,
                change_summary="Re-imported — data changed." if version_changed else "Initial import.",
            )
        )

        dataset.status = DatasetStatus.PROFILING
        db.commit()

        _profile_and_score(db, dataset, tables)

        dataset.status = DatasetStatus.READY
        db.commit()
    except Exception as exc:  # noqa: BLE001 — any failure must land the dataset in FAILED, never crash silently
        logger.exception("Dataset import failed for dataset_id=%s", dataset_id)
        db.rollback()
        dataset = db.get(Dataset, dataset_id)
        if dataset is not None:
            dataset.status = DatasetStatus.FAILED
            dataset.status_message = str(exc)[:2000]
            db.commit()
    # Raw files under data/raw/ are intentionally kept (audit trail + re-processing), win or fail.


def reprofile_dataset(db: Session, dataset_id: str) -> None:
    """Re-runs profiling/quality scoring against a dataset's existing
    tables without touching the underlying files — used by the manual
    "re-profile" action (section 44: `POST /datasets/{id}/profile`)."""
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        return
    tables = list(dataset.tables)
    if not tables:
        return
    try:
        dataset.status = DatasetStatus.PROFILING
        db.commit()
        _profile_and_score(db, dataset, tables)
        dataset.status = DatasetStatus.READY
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Re-profiling failed for dataset_id=%s", dataset_id)
        db.rollback()
        dataset = db.get(Dataset, dataset_id)
        if dataset is not None:
            dataset.status = DatasetStatus.FAILED
            dataset.status_message = str(exc)[:2000]
            db.commit()
