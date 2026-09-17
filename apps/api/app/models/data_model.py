from sqlalchemy import JSON, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataModelKind, DataModelRelationshipType, DataModelTableType


class DataModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A saved node/edge graph (spec section 60) — the same three tables
    back the Data Modeler (DIMENSIONAL), the Architecture Diagram Builder
    (ARCHITECTURE), and the Pipeline Playground's saved graphs (PIPELINE);
    `model_kind` is the only thing that changes how nodes/edges are
    interpreted and validated (see app/data_modeling/validation.py)."""

    __tablename__ = "data_models"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_kind: Mapped[DataModelKind] = mapped_column(Enum(DataModelKind, native_enum=False, length=20))

    tables: Mapped[list["DataModelTable"]] = relationship(
        back_populates="data_model", cascade="all, delete-orphan", order_by="DataModelTable.created_at"
    )
    relationships_: Mapped[list["DataModelRelationship"]] = relationship(
        back_populates="data_model", cascade="all, delete-orphan"
    )


class DataModelTable(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One node (a table, or an architecture/pipeline stage). `columns` is a
    JSON list of `{name, data_type, is_primary_key, is_foreign_key,
    references_table, references_column}` dicts — always read/written as a
    whole set with the table, never queried independently, so a fourth
    normalized table would add ceremony without a real benefit."""

    __tablename__ = "data_model_tables"

    data_model_id: Mapped[str] = mapped_column(
        ForeignKey("data_models.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    table_type: Mapped[DataModelTableType] = mapped_column(
        Enum(DataModelTableType, native_enum=False, length=20), default=DataModelTableType.OTHER
    )
    grain: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    columns: Mapped[list] = mapped_column(JSON, default=list)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)

    data_model: Mapped["DataModel"] = relationship(back_populates="tables")


class DataModelRelationship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One edge between two DataModelTable nodes within the same DataModel."""

    __tablename__ = "data_model_relationships"

    data_model_id: Mapped[str] = mapped_column(
        ForeignKey("data_models.id", ondelete="CASCADE"), index=True
    )
    from_table_id: Mapped[str] = mapped_column(
        ForeignKey("data_model_tables.id", ondelete="CASCADE"), index=True
    )
    to_table_id: Mapped[str] = mapped_column(
        ForeignKey("data_model_tables.id", ondelete="CASCADE"), index=True
    )
    from_column: Mapped[str | None] = mapped_column(String(150), nullable=True)
    to_column: Mapped[str | None] = mapped_column(String(150), nullable=True)
    relationship_type: Mapped[DataModelRelationshipType] = mapped_column(
        Enum(DataModelRelationshipType, native_enum=False, length=20),
        default=DataModelRelationshipType.ONE_TO_MANY,
    )
    label: Mapped[str | None] = mapped_column(String(200), nullable=True)

    data_model: Mapped["DataModel"] = relationship(back_populates="relationships_")
