"use client";

import { useState } from "react";
import { ArrowRight, Plus, Trash2, Waypoints } from "lucide-react";
import type { Dataset } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Select } from "@/components/ui/select";
import {
  useAddRelationship,
  useDatasetRelationships,
  useDeleteRelationship,
} from "@/features/datasets/use-dataset-relationships";

export function RelationshipsPanel({ dataset }: { dataset: Dataset }) {
  const relationshipsQuery = useDatasetRelationships(dataset.slug);
  const addMutation = useAddRelationship(dataset.slug);
  const deleteMutation = useDeleteRelationship(dataset.slug);

  const tableNames = dataset.tables.map((t) => t.table_name);
  const [fromTable, setFromTable] = useState(tableNames[0] ?? "");
  const [fromColumn, setFromColumn] = useState("");
  const [toTable, setToTable] = useState(tableNames[1] ?? tableNames[0] ?? "");
  const [toColumn, setToColumn] = useState("");

  const canAdd = fromTable && fromColumn.trim() && toTable && toColumn.trim();

  function handleAdd() {
    if (!canAdd) return;
    addMutation.mutate(
      { from_table: fromTable, from_column: fromColumn.trim(), to_table: toTable, to_column: toColumn.trim() },
      {
        onSuccess: () => {
          setFromColumn("");
          setToColumn("");
        },
      },
    );
  }

  if (dataset.tables.length < 2) {
    return (
      <EmptyState
        icon={Waypoints}
        title="Relationships need at least two tables"
        description="Import related files together as a collection to define relationships between them."
      />
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="mb-3 text-sm font-semibold text-foreground">Declare a relationship</p>
        <div className="flex flex-wrap items-end gap-2">
          <Select value={fromTable} onChange={(e) => setFromTable(e.target.value)} className="w-32">
            {tableNames.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
          <input
            value={fromColumn}
            onChange={(e) => setFromColumn(e.target.value)}
            placeholder="column"
            className="h-9 w-32 rounded-md border border-input bg-transparent px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
          />
          <ArrowRight className="mb-2 size-4 shrink-0 text-muted-foreground" />
          <Select value={toTable} onChange={(e) => setToTable(e.target.value)} className="w-32">
            {tableNames.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
          <input
            value={toColumn}
            onChange={(e) => setToColumn(e.target.value)}
            placeholder="column"
            className="h-9 w-32 rounded-md border border-input bg-transparent px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
          />
          <Button size="sm" onClick={handleAdd} disabled={!canAdd || addMutation.isPending}>
            <Plus className="size-4" aria-hidden="true" />
            Add
          </Button>
        </div>
      </div>

      {relationshipsQuery.isLoading ? (
        <LoadingState count={2} itemClassName="h-12" />
      ) : relationshipsQuery.isError ? (
        <ErrorState
          title="Unable to load relationships"
          message="We couldn't reach the API to load this dataset's relationships."
          retry={() => void relationshipsQuery.refetch()}
        />
      ) : !relationshipsQuery.data || relationshipsQuery.data.length === 0 ? (
        <EmptyState
          icon={Waypoints}
          title="No relationships defined yet"
          description="Declare how tables in this collection relate — e.g. orders.customer_id → customers.customer_id."
        />
      ) : (
        <ul className="flex flex-col gap-2">
          {relationshipsQuery.data.map((rel) => (
            <li
              key={rel.id}
              className="flex items-center justify-between gap-2 rounded-lg border border-border p-3 font-mono text-sm"
            >
              <span>
                {rel.from_table}.{rel.from_column} <ArrowRight className="inline size-3.5" /> {rel.to_table}.
                {rel.to_column}
              </span>
              <button
                type="button"
                onClick={() => deleteMutation.mutate(rel.id)}
                aria-label="Delete relationship"
                className="rounded p-1 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="size-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
