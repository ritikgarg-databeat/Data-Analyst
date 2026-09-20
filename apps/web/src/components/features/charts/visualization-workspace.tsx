"use client";

import { useState } from "react";
import { BarChart3, Trash2 } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Select } from "@/components/ui/select";
import { useDatasets } from "@/features/datasets/use-datasets";
import { useDatasetSchema } from "@/features/datasets/use-dataset-schema";
import { useCharts, useCreateChart, useDeleteChart } from "@/features/charts/use-charts";

import type { ChartDraft } from "./chart-builder";
import { ChartBuilder } from "./chart-builder";
import { ChartViewer } from "./chart-viewer";

export function VisualizationWorkspace({ initialDatasetId }: { initialDatasetId?: string }) {
  const datasetsQuery = useDatasets();
  const readyDatasets = (datasetsQuery.data ?? []).filter((d) => d.status === "READY" && d.tables.length > 0);

  const [selectedDatasetId, setSelectedDatasetId] = useState(initialDatasetId ?? "");
  // The active dataset defaults to the first ready one until the user explicitly
  // picks a different one — derived directly during render rather than mirrored
  // into state via an effect (same pattern as python-lab-page.tsx).
  const datasetId = selectedDatasetId || readyDatasets[0]?.id || "";
  const dataset = readyDatasets.find((d) => d.id === datasetId);
  const [tableName, setTableName] = useState<string | undefined>(undefined);
  const activeTable = tableName ?? dataset?.tables[0]?.table_name;

  const schemaQuery = useDatasetSchema(dataset?.slug, activeTable);
  const chartsQuery = useCharts(datasetId || undefined);
  const createChart = useCreateChart();
  const deleteChart = useDeleteChart();
  const [activeChartId, setActiveChartId] = useState<string | null>(null);

  function handleCreate(draft: ChartDraft) {
    if (!dataset || !activeTable) return;
    createChart.mutate(
      { dataset_id: dataset.id, table_name: activeTable, chart_type: draft.chartType, title: draft.title, config: draft.config },
      { onSuccess: (chart) => setActiveChartId(chart.id) },
    );
  }

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
        icon={BarChart3}
        title="No datasets ready to visualize"
        description="Import a dataset from the Dataset Hub first, then come back here to build charts."
      />
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-card p-3">
        <div className="flex w-full flex-col gap-1 sm:w-auto">
          <label htmlFor="viz-dataset" className="text-xs font-medium text-muted-foreground">
            Dataset
          </label>
          <Select
            id="viz-dataset"
            value={datasetId}
            onChange={(e) => {
              setSelectedDatasetId(e.target.value);
              setTableName(undefined);
              setActiveChartId(null);
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
            <label htmlFor="viz-table" className="text-xs font-medium text-muted-foreground">
              Table
            </label>
            <Select
              id="viz-table"
              value={activeTable}
              onChange={(e) => {
                setTableName(e.target.value);
                setActiveChartId(null);
              }}
              className="w-full sm:w-44"
            >
              {dataset.tables.map((t) => (
                <option key={t.table_name} value={t.table_name}>
                  {t.table_name}
                </option>
              ))}
            </Select>
          </div>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[18rem_1fr_14rem]">
        <div>
          {schemaQuery.data?.[0] ? (
            <ChartBuilder columns={schemaQuery.data[0].columns} onCreate={handleCreate} isCreating={createChart.isPending} />
          ) : (
            <LoadingState count={1} itemClassName="h-80" />
          )}
        </div>

        <div>
          {activeChartId ? (
            <ChartViewer chartId={activeChartId} />
          ) : (
            <EmptyState
              icon={BarChart3}
              title="No chart yet"
              description="Configure the chart builder on the left, then click Create Chart to preview it here."
            />
          )}
        </div>

        <aside className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3">
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Saved Charts</p>
          {chartsQuery.data && chartsQuery.data.length > 0 ? (
            <ul className="flex flex-col gap-1">
              {chartsQuery.data.map((chart) => (
                <li key={chart.id} className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setActiveChartId(chart.id)}
                    className={`flex-1 truncate rounded-md px-2 py-1.5 text-left text-sm ${
                      activeChartId === chart.id ? "bg-accent text-accent-foreground" : "hover:bg-accent/50"
                    }`}
                  >
                    {chart.title}
                  </button>
                  <button
                    type="button"
                    aria-label={`Delete ${chart.title}`}
                    onClick={() => {
                      deleteChart.mutate(chart.id);
                      if (activeChartId === chart.id) setActiveChartId(null);
                    }}
                    className="shrink-0 rounded p-1 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="size-3.5" />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground">No charts saved for this dataset yet.</p>
          )}
        </aside>
      </div>
    </div>
  );
}
