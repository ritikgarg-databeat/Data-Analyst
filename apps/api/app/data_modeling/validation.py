"""Model validation for the Data Modeler / Architecture Diagram Builder /
Pipeline Playground — one engine shared across all three `DataModelKind`s
(see DataModel's docstring). Findings are deliberately educational nudges
("a fact table usually has a grain"), not hard blocks — spec section 61:
"warnings should be educational rather than absolute rules". The exceptions
are the handful of checks that are actual structural breakage (a
relationship pointing at a table that doesn't exist) — those are
severity="error", everything else is severity="warning".
"""

from __future__ import annotations

from dataclasses import dataclass

from app.data_modeling.graph import build_adjacency, find_one_cycle
from app.models.data_model import DataModelRelationship, DataModelTable
from app.models.enums import DataModelKind

_MEASURE_NAME_HINTS = (
    "amount",
    "total",
    "revenue",
    "cost",
    "margin",
    "price",
    "count",
    "sum",
    "qty",
    "quantity",
)
_NUMERIC_TYPE_HINTS = ("int", "float", "double", "decimal", "numeric", "real")


@dataclass
class ValidationFinding:
    severity: str  # "error" | "warning"
    code: str
    message: str
    table_id: str | None = None
    table_name: str | None = None


def validate_model(
    model_kind: DataModelKind,
    tables: list[DataModelTable],
    relationships: list[DataModelRelationship],
) -> list[ValidationFinding]:
    tables_by_id = {t.id: t for t in tables}
    findings: list[ValidationFinding] = []

    findings += _check_duplicate_columns(tables)
    findings += _check_foreign_keys(tables)
    findings += _check_dangling_relationships(tables_by_id, relationships)
    findings += _check_relationship_columns(tables_by_id, relationships)
    findings += _check_cycles(model_kind, tables_by_id, relationships)

    if model_kind == DataModelKind.DIMENSIONAL:
        findings += _check_missing_primary_keys(tables)
        findings += _check_fact_tables_have_grain(tables)
        findings += _check_dimension_measures(tables)

    return findings


def _check_duplicate_columns(tables: list[DataModelTable]) -> list[ValidationFinding]:
    findings = []
    for table in tables:
        names = [str(c.get("name", "")).strip().lower() for c in table.columns if c.get("name")]
        duplicates = {name for name in names if names.count(name) > 1}
        for name in duplicates:
            findings.append(
                ValidationFinding(
                    severity="warning",
                    code="duplicate_column",
                    message=f"Column '{name}' appears more than once in '{table.name}'.",
                    table_id=table.id,
                    table_name=table.name,
                )
            )
    return findings


def _check_missing_primary_keys(tables: list[DataModelTable]) -> list[ValidationFinding]:
    findings = []
    for table in tables:
        has_pk = any(c.get("is_primary_key") for c in table.columns)
        if not has_pk:
            findings.append(
                ValidationFinding(
                    severity="warning",
                    code="missing_primary_key",
                    message=f"'{table.name}' has no column marked as a primary key. Most tables need "
                    "one so each row can be uniquely identified and safely referenced by other tables.",
                    table_id=table.id,
                    table_name=table.name,
                )
            )
    return findings


def _check_foreign_keys(tables: list[DataModelTable]) -> list[ValidationFinding]:
    findings = []
    tables_by_name = {t.name.strip().lower(): t for t in tables}
    for table in tables:
        for column in table.columns:
            if not column.get("is_foreign_key"):
                continue
            col_name = column.get("name", "<unnamed column>")
            ref_table_name = column.get("references_table")
            ref_column_name = column.get("references_column")
            if not ref_table_name:
                findings.append(
                    ValidationFinding(
                        severity="warning",
                        code="foreign_key_missing_target",
                        message=f"'{table.name}.{col_name}' is marked as a foreign key but doesn't say "
                        "which table it references.",
                        table_id=table.id,
                        table_name=table.name,
                    )
                )
                continue
            target = tables_by_name.get(str(ref_table_name).strip().lower())
            if target is None:
                findings.append(
                    ValidationFinding(
                        severity="warning",
                        code="foreign_key_unknown_table",
                        message=f"'{table.name}.{col_name}' references table '{ref_table_name}', which "
                        "isn't part of this model.",
                        table_id=table.id,
                        table_name=table.name,
                    )
                )
                continue
            if ref_column_name:
                target_columns = {str(c.get("name", "")).strip().lower() for c in target.columns}
                if str(ref_column_name).strip().lower() not in target_columns:
                    findings.append(
                        ValidationFinding(
                            severity="warning",
                            code="foreign_key_unknown_column",
                            message=f"'{table.name}.{col_name}' references "
                            f"'{ref_table_name}.{ref_column_name}', but '{target.name}' has no column "
                            "by that name.",
                            table_id=table.id,
                            table_name=table.name,
                        )
                    )
    return findings


def _check_dangling_relationships(
    tables_by_id: dict[str, DataModelTable], relationships: list[DataModelRelationship]
) -> list[ValidationFinding]:
    findings = []
    for rel in relationships:
        if rel.from_table_id not in tables_by_id or rel.to_table_id not in tables_by_id:
            findings.append(
                ValidationFinding(
                    severity="error",
                    code="dangling_relationship",
                    message="A relationship references a table that no longer exists in this model.",
                )
            )
    return findings


def _check_relationship_columns(
    tables_by_id: dict[str, DataModelTable], relationships: list[DataModelRelationship]
) -> list[ValidationFinding]:
    findings = []
    for rel in relationships:
        from_table = tables_by_id.get(rel.from_table_id)
        to_table = tables_by_id.get(rel.to_table_id)
        if from_table and rel.from_column:
            names = {str(c.get("name", "")).strip().lower() for c in from_table.columns}
            if rel.from_column.strip().lower() not in names:
                findings.append(
                    ValidationFinding(
                        severity="warning",
                        code="relationship_unknown_column",
                        message=f"Relationship references '{from_table.name}.{rel.from_column}', which "
                        "doesn't exist on that table.",
                        table_id=from_table.id,
                        table_name=from_table.name,
                    )
                )
        if to_table and rel.to_column:
            names = {str(c.get("name", "")).strip().lower() for c in to_table.columns}
            if rel.to_column.strip().lower() not in names:
                findings.append(
                    ValidationFinding(
                        severity="warning",
                        code="relationship_unknown_column",
                        message=f"Relationship references '{to_table.name}.{rel.to_column}', which "
                        "doesn't exist on that table.",
                        table_id=to_table.id,
                        table_name=to_table.name,
                    )
                )
    return findings


def _check_cycles(
    model_kind: DataModelKind,
    tables_by_id: dict[str, DataModelTable],
    relationships: list[DataModelRelationship],
) -> list[ValidationFinding]:
    # Only dangling-free edges make a meaningful graph.
    clean_relationships = [
        r for r in relationships if r.from_table_id in tables_by_id and r.to_table_id in tables_by_id
    ]
    adjacency = build_adjacency(clean_relationships)
    cycle = find_one_cycle(adjacency)
    if cycle is None:
        return []

    names = [tables_by_id[node_id].name for node_id in cycle if node_id in tables_by_id]
    path = " -> ".join(names)
    # A pipeline's edges are execution dependencies — a cycle there means the
    # pipeline could never actually run, so it's a real error, not a nudge.
    severity = "error" if model_kind == DataModelKind.PIPELINE else "warning"
    return [
        ValidationFinding(
            severity=severity,
            code="circular_relationship",
            message=f"Circular relationship detected: {path}.",
        )
    ]


def _check_fact_tables_have_grain(tables: list[DataModelTable]) -> list[ValidationFinding]:
    findings = []
    for table in tables:
        if table.table_type.value == "FACT" and not (table.grain or "").strip():
            findings.append(
                ValidationFinding(
                    severity="warning",
                    code="fact_table_missing_grain",
                    message=f"'{table.name}' is a fact table but has no grain defined. Naming the grain "
                    "(e.g. \"1 row = 1 order\") is what keeps a fact table's numbers additive and "
                    "unambiguous.",
                    table_id=table.id,
                    table_name=table.name,
                )
            )
    return findings


def _check_dimension_measures(tables: list[DataModelTable]) -> list[ValidationFinding]:
    findings = []
    for table in tables:
        if table.table_type.value != "DIMENSION":
            continue
        for column in table.columns:
            name = str(column.get("name", "")).lower()
            data_type = str(column.get("data_type", "")).lower()
            looks_numeric = any(hint in data_type for hint in _NUMERIC_TYPE_HINTS)
            looks_like_measure = any(hint in name for hint in _MEASURE_NAME_HINTS)
            if looks_numeric and looks_like_measure:
                findings.append(
                    ValidationFinding(
                        severity="warning",
                        code="dimension_looks_like_measure",
                        message=f"'{table.name}.{column.get('name')}' looks like it could be a "
                        "measure (a number you'd sum/average), which usually belongs on a fact table "
                        "rather than a dimension.",
                        table_id=table.id,
                        table_name=table.name,
                    )
                )
    return findings
