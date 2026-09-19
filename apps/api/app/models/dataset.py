from datetime import UTC, datetime

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DatasetSourceType, DatasetStatus, DifficultyLevel


class Dataset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A dataset available for practice/analysis/EDA — local sample data,
    a user-imported local file/folder, or a Kaggle download.

    Phase 1-4 fields (name, slug, description, source, source_url, domain,
    file_path, file_format, row_count, column_count, difficulty,
    dataset_metadata) are untouched so SQL Lab (app/sql/registry.py) and
    Python Lab (app/python_lab/service.py) keep working unmodified — both
    read `Dataset` + `SqlTable` directly. Phase 5 fields below are additive.

    A dataset with more than one `DatasetTable` child is what the product
    spec calls a "dataset collection" (e.g. the seeded "ecommerce" dataset,
    which already works this way via `SqlTable`) — deliberately not a
    separate `DatasetCollection` model, to avoid two parallel ways of
    representing the same "one Dataset, many tables" shape.
    """

    __tablename__ = "datasets"

    # NULL identifies a built-in shared dataset. Imported datasets belong to
    # exactly one user and are never visible to another learner.
    owner_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, native_enum=False, length=20), default=DifficultyLevel.BEGINNER
    )
    # Mapped to Python attribute `dataset_metadata` because `metadata` is reserved
    # by SQLAlchemy's declarative Base; the JSON column itself is still named
    # "metadata" so the API schema field stays `metadata`.
    dataset_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # --- Phase 5 additions -------------------------------------------------
    source_type: Mapped[DatasetSourceType] = mapped_column(
        Enum(DatasetSourceType, native_enum=False, length=20), default=DatasetSourceType.LOCAL
    )
    # Catalog facet ("E-commerce", "Finance", "Marketing"...) shown as filter
    # chips on the Dataset Hub — deliberately separate from `domain`, which
    # is an unrelated legacy field some seeded rows use to reference a
    # curriculum domain slug (e.g. "sql", "business-analytics").
    business_domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    license: Mapped[str | None] = mapped_column(String(150), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus, native_enum=False, length=20), default=DatasetStatus.READY
    )
    status_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_profiled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # "<owner>/<dataset-slug>" — set only for source_type == KAGGLE, kept so a
    # dataset can later be re-synced against the same Kaggle listing.
    kaggle_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tables: Mapped[list["DatasetTable"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", order_by="DatasetTable.display_order"
    )


class DatasetTable(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One file/table within a Dataset — the Phase 5 general-purpose anchor
    for profiling, quality, and relationships. Deliberately independent of
    `SqlTable` (app/models/sql_lab.py): importing a dataset through the
    Dataset Hub creates both a `DatasetTable` (this) and a matching
    `SqlTable` row pointing at the same file, so newly imported datasets are
    immediately queryable in the SQL Lab and listed in the Python Lab for
    free, with zero changes to either subsystem."""

    __tablename__ = "dataset_tables"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(500))  # repo-root-relative
    file_format: Mapped[str] = mapped_column(String(20))  # csv | parquet | json
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    grain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    dataset: Mapped["Dataset"] = relationship(back_populates="tables")


class DatasetVersion(UUIDPrimaryKeyMixin, Base):
    """One point-in-time fingerprint of a Dataset's data, appended on every
    (re)import — see app/dataset_hub/import_service.py. Deliberately simple
    (metadata + reference only, no stored diffs/snapshots — not git-like
    versioning, per the Phase 5 spec)."""

    __tablename__ = "dataset_versions"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    fingerprint: Mapped[str] = mapped_column(String(64))
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class DatasetRelationship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user- or import-declared foreign-key-shaped link between two tables
    within the same dataset collection — metadata only (section 31 of the
    Phase 5 spec deliberately stops short of a full data-modeling engine)."""

    __tablename__ = "dataset_relationships"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    from_table: Mapped[str] = mapped_column(String(100))
    from_column: Mapped[str] = mapped_column(String(150))
    to_table: Mapped[str] = mapped_column(String(100))
    to_column: Mapped[str] = mapped_column(String(150))
    relationship_type: Mapped[str] = mapped_column(String(20), default="one_to_many")


class DatasetNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A personal note at the dataset, table, or column level (chart-level
    notes are covered by Chart.insight_* fields instead — see
    app/models/chart.py). Exactly one of table_name/column_name is set for a
    table/column-scoped note; both null means a dataset-level note."""

    __tablename__ = "dataset_notes"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    column_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    body: Mapped[str] = mapped_column(Text)
