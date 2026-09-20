"use client";

import { useState } from "react";
import { Rocket } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Select } from "@/components/ui/select";
import { useDatasetRawSchema } from "@/features/datasets/use-dataset-analysis";
import { useDatasets } from "@/features/datasets/use-datasets";

import { CohortRetentionExplorer } from "./cohort-retention-explorer";
import { FunnelAnalyzer } from "./funnel-analyzer";

type Tab = "funnel" | "cohort";

export function ProductAnalyticsWorkspace() {
  const datasetsQuery = useDatasets();
  const readyDatasets = (datasetsQuery.data ?? []).filter((d) => d.status === "READY");

  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const preferredDataset = readyDatasets.find((d) => d.slug === "saas-product") ?? readyDatasets[0];
  const datasetId = selectedDatasetId || preferredDataset?.id || "";
  const dataset = readyDatasets.find((d) => d.id === datasetId);

  const [tableName, setTableName] = useState<string | undefined>(undefined);
  const preferredTable = dataset?.tables.find((t) => t.table_name === "events") ?? dataset?.tables[0];
  const activeTable = tableName ?? preferredTable?.table_name;

  const [tab, setTab] = useState<Tab>("funnel");
  const schemaQuery = useDatasetRawSchema(dataset?.slug, activeTable);
  const columns = schemaQuery.data?.columns ?? [];

  if (datasetsQuery.isLoading) return <LoadingState count={1} itemClassName="h-96" />;
  if (datasetsQuery.isError) {
    return (
      <ErrorState
        title="Unable to load datasets"
        message="We couldn't reach the API to load your datasets."
        retry={() => void datasetsQuery.refetch()}
      />
    );
  }

  if (readyDatasets.length === 0) {
    return (
      <EmptyState
        icon={Rocket}
        title="No datasets ready to analyze"
        description="Import a dataset from the Dataset Hub first, then come back here for funnel and cohort analysis."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-3">
        <div className="flex w-full flex-col gap-1 sm:w-auto">
          <label htmlFor="pa-dataset" className="text-xs font-medium text-muted-foreground">
            Dataset
          </label>
          <Select
            id="pa-dataset"
            value={datasetId}
            onChange={(e) => {
              setSelectedDatasetId(e.target.value);
              setTableName(undefined);
            }}
            className="w-full sm:w-56"
          >
            {readyDatasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </div>
        {dataset && dataset.tables.length > 1 ? (
          <div className="flex w-full flex-col gap-1 sm:w-auto">
            <label htmlFor="pa-table" className="text-xs font-medium text-muted-foreground">
              Table
            </label>
            <Select id="pa-table" value={activeTable} onChange={(e) => setTableName(e.target.value)} className="w-full sm:w-44">
              {dataset.tables.map((t) => (
                <option key={t.table_name} value={t.table_name}>
                  {t.table_name}
                </option>
              ))}
            </Select>
          </div>
        ) : null}
      </div>

      <div role="tablist" className="flex flex-wrap gap-1 border-b border-border">
        {(
          [
            { key: "funnel", label: "Funnel Analyzer" },
            { key: "cohort", label: "Cohort Retention" },
          ] as const
        ).map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {schemaQuery.isLoading ? (
          <LoadingState count={1} itemClassName="h-72" />
        ) : schemaQuery.isError ? (
          <ErrorState
            title="Unable to load table schema"
            message="We couldn't reach the API to load this table's columns."
            retry={() => void schemaQuery.refetch()}
          />
        ) : columns.length === 0 ? (
          <p className="text-sm text-muted-foreground">This table hasn&apos;t been profiled yet.</p>
        ) : tab === "funnel" ? (
          <FunnelAnalyzer datasetId={datasetId} tableName={activeTable!} columns={columns} />
        ) : (
          <CohortRetentionExplorer datasetId={datasetId} tableName={activeTable!} columns={columns} />
        )}
      </div>
    </div>
  );
}
