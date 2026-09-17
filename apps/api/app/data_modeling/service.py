"""CRUD + validation orchestration for DataModel graphs — one service shared
by the Data Modeler, Architecture Diagram Builder, and Pipeline Playground
routers (they differ only in which `model_kind` they pass through)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError, NotFoundError
from app.data_modeling import validation
from app.data_modeling.validation import ValidationFinding
from app.models.data_model import DataModel, DataModelRelationship, DataModelTable
from app.models.enums import DataModelKind, DataModelRelationshipType, DataModelTableType


class DataModelService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_models(self, user_id: str, model_kind: DataModelKind | None = None) -> list[DataModel]:
        stmt = select(DataModel).where(DataModel.user_id == user_id)
        if model_kind is not None:
            stmt = stmt.where(DataModel.model_kind == model_kind)
        stmt = stmt.order_by(DataModel.updated_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_model(self, user_id: str, model_id: str) -> DataModel:
        stmt = (
            select(DataModel)
            .where(DataModel.id == model_id)
            .options(selectinload(DataModel.tables), selectinload(DataModel.relationships_))
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None or model.user_id != user_id:
            raise NotFoundError(f"Data model '{model_id}' not found.")
        return model

    def create_model(
        self, user_id: str, *, name: str, description: str | None, model_kind: DataModelKind
    ) -> DataModel:
        model = DataModel(user_id=user_id, name=name, description=description, model_kind=model_kind)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def update_model(
        self, user_id: str, model_id: str, *, name: str | None = None, description: str | None = None
    ) -> DataModel:
        model = self.get_model(user_id, model_id)
        if name is not None:
            model.name = name
        if description is not None:
            model.description = description
        self.db.commit()
        self.db.refresh(model)
        return model

    def delete_model(self, user_id: str, model_id: str) -> None:
        model = self.get_model(user_id, model_id)
        self.db.delete(model)
        self.db.commit()

    def replace_graph(
        self,
        user_id: str,
        model_id: str,
        *,
        tables: list[dict],
        relationships: list[dict],
    ) -> DataModel:
        """Wholesale-replaces every table/relationship in the model with the
        given set — the same "save the whole graph" approach as Chart.config
        (Phase 5): a canvas editor's natural unit of save is the whole
        diagram, not incremental node-by-node diffs. `tables` entries carry a
        client-assigned `key` (not a DB id, which doesn't exist yet) so
        `relationships` can say which tables they connect within the same
        request."""
        model = self.get_model(user_id, model_id)
        model.tables.clear()
        model.relationships_.clear()
        self.db.flush()

        key_to_table: dict[str, DataModelTable] = {}
        for entry in tables:
            key = entry["key"]
            table = DataModelTable(
                data_model_id=model.id,
                name=entry["name"],
                table_type=DataModelTableType(entry.get("table_type", DataModelTableType.OTHER.value)),
                grain=entry.get("grain"),
                notes=entry.get("notes"),
                columns=entry.get("columns", []),
                position_x=entry.get("position_x", 0.0),
                position_y=entry.get("position_y", 0.0),
            )
            self.db.add(table)
            key_to_table[key] = table
        self.db.flush()  # assigns real ids to the new DataModelTable rows

        for entry in relationships:
            from_table = key_to_table.get(entry["from_key"])
            to_table = key_to_table.get(entry["to_key"])
            if from_table is None or to_table is None:
                raise AppError("A relationship references a table key that isn't in this save request.")
            self.db.add(
                DataModelRelationship(
                    data_model_id=model.id,
                    from_table_id=from_table.id,
                    to_table_id=to_table.id,
                    from_column=entry.get("from_column"),
                    to_column=entry.get("to_column"),
                    relationship_type=DataModelRelationshipType(
                        entry.get("relationship_type", DataModelRelationshipType.ONE_TO_MANY.value)
                    ),
                    label=entry.get("label"),
                )
            )

        self.db.commit()
        # `model` is still the same identity-mapped object get_model's
        # selectinload populated *before* the clear()/add() above — its
        # `.tables`/`.relationships_` collections won't pick up the new rows
        # on their own, since SQLAlchemy doesn't assume an already-loaded
        # collection needs re-fetching. Expire it so the next get_model
        # re-reads the graph as it now actually is in the database.
        self.db.expire(model)
        return self.get_model(user_id, model_id)

    def validate_model(self, user_id: str, model_id: str) -> list[ValidationFinding]:
        model = self.get_model(user_id, model_id)
        return validation.validate_model(model.model_kind, model.tables, model.relationships_)
