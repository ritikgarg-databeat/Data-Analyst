"""The Dataset Hub's catalog + import + collection-metadata service.

Background import (`start_local_import`, `start_kaggle_import`, `reimport`,
`trigger_reprofile`) all hand a `BackgroundTasks` a closure over `self.db` —
the SAME request-scoped `Session` FastAPI's `Depends(get_db)` yielded. This
is deliberate and relies on a specific, documented FastAPI guarantee: a
dependency-with-yield's cleanup (closing the session) runs *after*
background tasks finish, not before — so the session is still open and
usable when the background task actually executes. See
app/python_lab/service.py's docstring for the sibling pattern this mirrors
(Docker instead of DuckDB), and tests/test_dataset_import.py, which proves
this works synchronously under TestClient (no polling needed in tests).
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError, NotFoundError
from app.dataset_hub import import_service
from app.dataset_hub.security import slugify
from app.models.chart import Chart
from app.models.dataset import Dataset, DatasetNote, DatasetRelationship, DatasetVersion
from app.models.dataset_profile import DatasetColumnProfile, DatasetProfile
from app.models.eda import EdaWorkspace
from app.models.enums import DatasetSourceType, DatasetStatus, DifficultyLevel, ExerciseType
from app.models.exercise import Exercise
from app.models.project import Project
from app.models.sql_lab import SqlTable
from app.models.tag import DatasetTag, Tag
from app.repositories.dataset import DatasetRepository
from app.schemas.dataset import (
    CreateNoteRequest,
    CreateRelationshipRequest,
    DatasetNoteSchema,
    DatasetRelationshipSchema,
    DatasetTableSchema,
    DatasetUsageSchema,
    DatasetVersionSchema,
    LocalImportForm,
)
from app.schemas.dataset import (
    Dataset as DatasetSchema,
)


@dataclass
class DatasetFilters:
    q: str | None = None
    business_domain: str | None = None
    source_type: str | None = None
    status: str | None = None
    tag: str | None = None


class DatasetService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.repo = DatasetRepository(db)

    # --- Catalog -----------------------------------------------------------

    def _tags_for(self, dataset_id: str) -> list[str]:
        stmt = (
            select(Tag.slug)
            .join(DatasetTag, DatasetTag.tag_id == Tag.id)
            .where(DatasetTag.dataset_id == dataset_id)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_datasets(self, filters: DatasetFilters | None = None) -> list[DatasetSchema]:
        filters = filters or DatasetFilters()
        stmt = select(Dataset)
        if filters.business_domain:
            stmt = stmt.where(Dataset.business_domain == filters.business_domain)
        if filters.source_type:
            stmt = stmt.where(Dataset.source_type == DatasetSourceType(filters.source_type))
        if filters.status:
            stmt = stmt.where(Dataset.status == DatasetStatus(filters.status))
        if filters.tag:
            stmt = (
                stmt.join(DatasetTag, DatasetTag.dataset_id == Dataset.id)
                .join(Tag, Tag.id == DatasetTag.tag_id)
                .where(Tag.slug == filters.tag)
            )

        datasets = list(self.db.execute(stmt.order_by(Dataset.name)).scalars().unique().all())

        if filters.q:
            needle = filters.q.strip().lower()
            column_match_ids = set(
                self.db.execute(
                    select(DatasetProfile.dataset_id)
                    .join(DatasetColumnProfile, DatasetColumnProfile.profile_id == DatasetProfile.id)
                    .where(DatasetColumnProfile.column_name.ilike(f"%{needle}%"))
                )
                .scalars()
                .all()
            )

            def _matches(d: Dataset) -> bool:
                if d.id in column_match_ids:
                    return True
                haystack = " ".join(
                    filter(
                        None,
                        [
                            d.name,
                            d.description,
                            d.domain,
                            d.business_domain,
                            d.source,
                            *self._tags_for(d.id),
                        ],
                    )
                ).lower()
                return needle in haystack

            datasets = [d for d in datasets if _matches(d)]

        return [self.to_schema(d) for d in datasets]

    def _find(self, id_or_slug: str) -> Dataset:
        dataset = self.repo.get_by_id(id_or_slug) or self.repo.get_by_slug(id_or_slug)
        if dataset is None:
            raise NotFoundError(f"Dataset '{id_or_slug}' was not found.", details={"id_or_slug": id_or_slug})
        return dataset

    def get(self, id_or_slug: str) -> DatasetSchema:
        return self.to_schema(self._find(id_or_slug))

    def to_schema(self, dataset: Dataset) -> DatasetSchema:
        schema = DatasetSchema.model_validate(dataset)
        schema.tags = self._tags_for(dataset.id)
        if dataset.tables:
            schema.tables = [DatasetTableSchema.model_validate(t) for t in dataset.tables]
        else:
            # Datasets seeded in Phase 1-4 (e.g. "ecommerce", "saas-product") only ever
            # got `SqlTable` rows (via app/sql/sync.py), never a Phase 5 `DatasetTable` —
            # without this fallback, callers that read `schema.tables` (the Visualization/
            # Product Analytics table pickers) would see an empty list and have no way to
            # select any table but the implicit default, even though the dataset is fully
            # queryable. `size_bytes` has no SqlTable equivalent, so it's always None here.
            stmt = (
                select(SqlTable)
                .where(SqlTable.dataset_id == dataset.id)
                .order_by(SqlTable.display_order)
            )
            sql_tables = self.db.execute(stmt).scalars().all()
            schema.tables = [
                DatasetTableSchema(
                    id=t.id,
                    table_name=t.table_name,
                    file_format=t.file_format,
                    row_count=t.row_count,
                    column_count=t.column_count,
                    size_bytes=None,
                    grain=t.grain,
                    display_order=t.display_order,
                )
                for t in sql_tables
            ]
        # "SQL/Python Ready" must reflect reality for datasets from *either*
        # generation: Phase 5 imports populate `dataset.tables` (DatasetTable);
        # the datasets seeded in Phase 1-4 (e.g. "ecommerce") only ever got
        # `SqlTable` rows (via app/sql/sync.py) and never a DatasetTable —
        # they are just as queryable in SQL Lab and just as loadable in
        # Python Lab (both read SqlTable directly), so this must check both.
        has_sql_tables = bool(dataset.tables) or self._count(SqlTable, dataset.id) > 0
        schema.sql_ready = has_sql_tables
        schema.python_ready = has_sql_tables or bool(dataset.file_path and dataset.file_format)
        return schema

    def get_by_slug(self, slug: str) -> DatasetSchema:
        """Kept for backward compatibility with the Phase 1-4 `/datasets/{slug}` contract."""
        return self.get(slug)

    # --- Tags ---------------------------------------------------------------

    def set_tags(self, dataset: Dataset, tag_slugs: list[str]) -> None:
        self.db.query(DatasetTag).filter(DatasetTag.dataset_id == dataset.id).delete()
        for slug in tag_slugs:
            tag = self.db.query(Tag).filter(Tag.slug == slug).one_or_none()
            if tag is None:
                tag = Tag(slug=slug, name=slug.replace("-", " ").title())
                self.db.add(tag)
                self.db.flush()
            self.db.add(DatasetTag(dataset_id=dataset.id, tag_id=tag.id))

    # --- Import --------------------------------------------------------------

    def _unique_slug(self, base: str) -> str:
        slug = slugify(base)
        candidate = slug
        suffix = 2
        while self.repo.get_by_slug(candidate) is not None:
            candidate = f"{slug}-{suffix}"
            suffix += 1
        return candidate

    def start_local_import(
        self, files: list[UploadFile], form: LocalImportForm, background_tasks: BackgroundTasks
    ) -> DatasetSchema:
        slug = self._unique_slug(form.name)
        # Stage (and validate) the upload BEFORE creating any Dataset row — an
        # unsupported extension, empty file, or oversized upload must fail
        # cleanly with nothing left behind, never an orphaned dataset stuck
        # in IMPORTING forever (see tests/test_dataset_import.py's
        # TestValidationErrors).
        staged = import_service.stage_uploads(files, slug, max_bytes=self.settings.dataset_max_upload_bytes)

        dataset = Dataset(
            name=form.name,
            slug=slug,
            description=form.description,
            business_domain=form.business_domain,
            difficulty=form.difficulty,
            source="local upload",
            source_type=DatasetSourceType.LOCAL,
            status=DatasetStatus.IMPORTING,
        )
        self.db.add(dataset)
        self.db.flush()
        self.set_tags(dataset, form.tags)
        self.db.commit()
        self.db.refresh(dataset)

        background_tasks.add_task(import_service.process_dataset_import, self.db, dataset.id, staged)
        return self.to_schema(dataset)

    def reimport(
        self, id_or_slug: str, files: list[UploadFile], background_tasks: BackgroundTasks
    ) -> DatasetSchema:
        dataset = self._find(id_or_slug)
        staged = import_service.stage_uploads(
            files, dataset.slug, max_bytes=self.settings.dataset_max_upload_bytes
        )
        background_tasks.add_task(import_service.process_dataset_import, self.db, dataset.id, staged)
        dataset.status = DatasetStatus.IMPORTING
        self.db.commit()
        return self.to_schema(dataset)

    def trigger_reprofile(self, id_or_slug: str, background_tasks: BackgroundTasks) -> DatasetSchema:
        dataset = self._find(id_or_slug)
        if not dataset.tables:
            raise AppError("This dataset has no tables to profile yet.")
        background_tasks.add_task(import_service.reprofile_dataset, self.db, dataset.id)
        dataset.status = DatasetStatus.PROFILING
        self.db.commit()
        return self.to_schema(dataset)

    def archive(self, id_or_slug: str) -> DatasetSchema:
        dataset = self._find(id_or_slug)
        dataset.status = DatasetStatus.ARCHIVED
        self.db.commit()
        return self.to_schema(dataset)

    # --- Relationships ---------------------------------------------------

    def list_relationships(self, id_or_slug: str) -> list[DatasetRelationshipSchema]:
        dataset = self._find(id_or_slug)
        stmt = select(DatasetRelationship).where(DatasetRelationship.dataset_id == dataset.id)
        return [DatasetRelationshipSchema.model_validate(r) for r in self.db.execute(stmt).scalars().all()]

    def add_relationship(
        self, id_or_slug: str, payload: CreateRelationshipRequest
    ) -> DatasetRelationshipSchema:
        dataset = self._find(id_or_slug)
        table_names = {t.table_name for t in dataset.tables}
        if payload.from_table not in table_names or payload.to_table not in table_names:
            raise AppError(
                "Both tables must belong to this dataset.", details={"tables": sorted(table_names)}
            )
        rel = DatasetRelationship(
            dataset_id=dataset.id,
            from_table=payload.from_table,
            from_column=payload.from_column,
            to_table=payload.to_table,
            to_column=payload.to_column,
            relationship_type=payload.relationship_type,
        )
        self.db.add(rel)
        self.db.commit()
        self.db.refresh(rel)
        return DatasetRelationshipSchema.model_validate(rel)

    def delete_relationship(self, id_or_slug: str, relationship_id: str) -> None:
        dataset = self._find(id_or_slug)
        rel = self.db.get(DatasetRelationship, relationship_id)
        if rel is None or rel.dataset_id != dataset.id:
            raise NotFoundError(f"Relationship '{relationship_id}' was not found.")
        self.db.delete(rel)
        self.db.commit()

    # --- Notes ---------------------------------------------------------

    def list_notes(self, id_or_slug: str) -> list[DatasetNoteSchema]:
        dataset = self._find(id_or_slug)
        stmt = (
            select(DatasetNote)
            .where(DatasetNote.dataset_id == dataset.id)
            .order_by(DatasetNote.created_at.desc())
        )
        return [DatasetNoteSchema.model_validate(n) for n in self.db.execute(stmt).scalars().all()]

    def add_note(self, id_or_slug: str, user_id: str, payload: CreateNoteRequest) -> DatasetNoteSchema:
        dataset = self._find(id_or_slug)
        note = DatasetNote(
            dataset_id=dataset.id,
            user_id=user_id,
            table_name=payload.table_name,
            column_name=payload.column_name,
            body=payload.body,
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return DatasetNoteSchema.model_validate(note)

    def delete_note(self, id_or_slug: str, note_id: str, user_id: str) -> None:
        dataset = self._find(id_or_slug)
        note = self.db.get(DatasetNote, note_id)
        if note is None or note.dataset_id != dataset.id or note.user_id != user_id:
            raise NotFoundError(f"Note '{note_id}' was not found.")
        self.db.delete(note)
        self.db.commit()

    # --- Versions ---------------------------------------------------------

    def list_versions(self, id_or_slug: str) -> list[DatasetVersionSchema]:
        dataset = self._find(id_or_slug)
        stmt = (
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset.id)
            .order_by(DatasetVersion.version.desc())
        )
        return [DatasetVersionSchema.model_validate(v) for v in self.db.execute(stmt).scalars().all()]

    # --- Usage ---------------------------------------------------------

    def _count(self, model, dataset_id: str) -> int:
        return self.db.execute(
            select(func.count()).select_from(model).where(model.dataset_id == dataset_id)
        ).scalar_one()

    def get_usage(self, id_or_slug: str) -> DatasetUsageSchema:
        dataset = self._find(id_or_slug)
        exercises = list(
            self.db.execute(select(Exercise).where(Exercise.dataset_id == dataset.id)).scalars().all()
        )
        sql_count = sum(1 for e in exercises if e.exercise_type == ExerciseType.SQL)
        python_count = sum(1 for e in exercises if e.exercise_type == ExerciseType.PYTHON)
        return DatasetUsageSchema(
            sql_exercises=sql_count,
            python_exercises=python_count,
            other_exercises=len(exercises) - sql_count - python_count,
            eda_workspaces=self._count(EdaWorkspace, dataset.id),
            charts=self._count(Chart, dataset.id),
            projects=self._count(Project, dataset.id),
        )

    # --- Kaggle finalize (used by app/services/kaggle_service.py) ----------

    def create_kaggle_dataset_shell(
        self,
        name: str,
        *,
        description: str | None,
        business_domain: str | None,
        tags: list[str],
        kaggle_ref: str,
    ) -> Dataset:
        slug = self._unique_slug(name)
        dataset = Dataset(
            name=name,
            slug=slug,
            description=description,
            business_domain=business_domain,
            source=f"Kaggle ({kaggle_ref})",
            source_url=f"https://www.kaggle.com/datasets/{kaggle_ref}",
            source_type=DatasetSourceType.KAGGLE,
            status=DatasetStatus.IMPORTING,
            kaggle_ref=kaggle_ref,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )
        self.db.add(dataset)
        self.db.flush()
        self.set_tags(dataset, tags)
        self.db.commit()
        self.db.refresh(dataset)
        return dataset
