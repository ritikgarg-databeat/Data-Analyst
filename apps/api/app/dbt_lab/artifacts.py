"""Parses dbt's own on-disk artifacts (target/manifest.json, catalog.json,
run_results.json) into structured data for the API. These files are dbt's
authoritative state — the app never duplicates them into its own database
(see DbtRun's docstring); this module is the only place that reads them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.dbt_lab.paths import DBT_TARGET_DIR

_MODEL_RESOURCE_TYPES = {"model", "seed", "snapshot"}


def _load_json(name: str) -> dict[str, Any] | None:
    path = DBT_TARGET_DIR / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_manifest() -> dict[str, Any] | None:
    return _load_json("manifest.json")


def get_catalog() -> dict[str, Any] | None:
    return _load_json("catalog.json")


def get_run_results() -> dict[str, Any] | None:
    return _load_json("run_results.json")


def get_node_result(unique_id: str) -> dict[str, Any] | None:
    """One node's outcome from the most recent run_results.json — used by
    dbt exercise grading (app/services/dbt_exercise_service.py) to check
    whether a submitted model actually built."""
    run_results = get_run_results()
    if run_results is None:
        return None
    return next((r for r in run_results.get("results", []) if r.get("unique_id") == unique_id), None)


@dataclass
class LineageNode:
    unique_id: str
    name: str
    resource_type: str  # model | seed | snapshot | source
    layer: str | None  # staging | intermediate | marts | None
    materialized: str | None
    description: str
    depends_on: list[str] = field(default_factory=list)


@dataclass
class LineageGraph:
    nodes: list[LineageNode]
    edges: list[tuple[str, str]]  # (upstream_unique_id, downstream_unique_id)
    generated_at: str | None


def build_lineage_graph() -> LineageGraph | None:
    """Builds the full project DAG (models + seeds + snapshots + the sources
    they read from) from manifest.json's own `depends_on`/`parent_map`
    fields — no duplicated dependency logic, just a reshape for the frontend
    DAG viewer."""
    manifest = get_manifest()
    if manifest is None:
        return None

    nodes: list[LineageNode] = []
    edges: list[tuple[str, str]] = []

    for unique_id, node in manifest.get("nodes", {}).items():
        resource_type = node.get("resource_type")
        if resource_type not in _MODEL_RESOURCE_TYPES:
            continue
        fqn = node.get("fqn") or []
        layer = fqn[1] if resource_type == "model" and len(fqn) > 2 else None
        depends_on = list((node.get("depends_on") or {}).get("nodes", []))
        nodes.append(
            LineageNode(
                unique_id=unique_id,
                name=node.get("name", unique_id),
                resource_type=resource_type,
                layer=layer,
                materialized=(node.get("config") or {}).get("materialized"),
                description=node.get("description") or "",
                depends_on=depends_on,
            )
        )
        for upstream in depends_on:
            edges.append((upstream, unique_id))

    for unique_id, source in manifest.get("sources", {}).items():
        nodes.append(
            LineageNode(
                unique_id=unique_id,
                name=source.get("name", unique_id),
                resource_type="source",
                layer=None,
                materialized=None,
                description=source.get("description") or "",
                depends_on=[],
            )
        )

    generated_at = (manifest.get("metadata") or {}).get("generated_at")
    return LineageGraph(nodes=nodes, edges=edges, generated_at=generated_at)


@dataclass
class ColumnDoc:
    name: str
    data_type: str | None
    description: str


@dataclass
class NodeDoc:
    unique_id: str
    name: str
    resource_type: str
    description: str
    materialized: str | None
    schema_name: str | None
    columns: list[ColumnDoc]
    test_unique_ids: list[str]


def build_docs() -> list[NodeDoc] | None:
    """Combines manifest.json (descriptions, which tests attach to which
    node) with catalog.json (actual column types, as executed) — the same
    join `dbt docs generate`'s own UI performs."""
    manifest = get_manifest()
    if manifest is None:
        return None
    catalog = get_catalog() or {}
    catalog_nodes: dict[str, Any] = catalog.get("nodes", {}) | catalog.get("sources", {})

    tests_by_upstream: dict[str, list[str]] = {}
    for unique_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") != "test":
            continue
        for upstream in (node.get("depends_on") or {}).get("nodes", []):
            tests_by_upstream.setdefault(upstream, []).append(unique_id)

    docs: list[NodeDoc] = []
    for unique_id, node in manifest.get("nodes", {}).items():
        if node.get("resource_type") not in _MODEL_RESOURCE_TYPES:
            continue
        catalog_entry = catalog_nodes.get(unique_id, {})
        catalog_columns = catalog_entry.get("columns", {})
        manifest_columns = node.get("columns", {})

        if catalog_columns:
            # catalog.json reflects the table/view as actually built — the
            # authoritative column list. manifest.json's own `columns` only
            # includes columns someone bothered to document in a schema.yml,
            # which is usually a subset (see e.g. fct_orders in marts.yml).
            ordered_names = sorted(catalog_columns, key=lambda n: catalog_columns[n].get("index", 0))
            columns = [
                ColumnDoc(
                    name=col_name,
                    data_type=catalog_columns[col_name].get("type"),
                    description=(manifest_columns.get(col_name) or {}).get("description") or "",
                )
                for col_name in ordered_names
            ]
        else:
            # No catalog yet (only `dbt compile` has run, never anything
            # that builds a real relation) — fall back to whatever columns
            # were documented, with no type information.
            columns = [
                ColumnDoc(name=col_name, data_type=None, description=col_meta.get("description") or "")
                for col_name, col_meta in manifest_columns.items()
            ]
        docs.append(
            NodeDoc(
                unique_id=unique_id,
                name=node.get("name", unique_id),
                resource_type=node.get("resource_type"),
                description=node.get("description") or "",
                materialized=(node.get("config") or {}).get("materialized"),
                schema_name=catalog_entry.get("metadata", {}).get("schema"),
                columns=columns,
                test_unique_ids=tests_by_upstream.get(unique_id, []),
            )
        )
    return docs


@dataclass
class TestResult:
    unique_id: str
    name: str
    status: str  # pass | fail | error | skipped
    failures: int | None
    message: str | None
    execution_time: float | None


def build_test_results() -> list[TestResult] | None:
    """From the most recent run_results.json — but ONLY when that artifact
    was actually written by `dbt test`/`dbt build`. Every dbt subcommand
    overwrites run_results.json, including `docs generate` and `compile` —
    both list test nodes too (they get compiled either way), but with a
    generic "success" compile status that would otherwise look
    indistinguishable from a real test pass. `args.which` (dbt's own record
    of which command produced this file) is what disambiguates."""
    manifest = get_manifest()
    run_results = get_run_results()
    if run_results is None:
        return None
    if (run_results.get("args") or {}).get("which") not in {"test", "build"}:
        return None

    test_names = {}
    if manifest is not None:
        test_names = {
            uid: n.get("name", uid)
            for uid, n in manifest.get("nodes", {}).items()
            if n.get("resource_type") == "test"
        }

    results: list[TestResult] = []
    for result in run_results.get("results", []):
        unique_id = result.get("unique_id", "")
        if not unique_id.startswith("test."):
            continue
        results.append(
            TestResult(
                unique_id=unique_id,
                name=test_names.get(unique_id, unique_id),
                status=result.get("status", "unknown"),
                failures=result.get("failures"),
                message=result.get("message"),
                execution_time=result.get("execution_time"),
            )
        )
    return results
