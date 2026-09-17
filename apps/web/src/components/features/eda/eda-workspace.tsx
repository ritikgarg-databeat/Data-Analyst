"use client";

import { HelpCircle, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useDataset } from "@/features/datasets/use-datasets";
import { useDatasetSchema } from "@/features/datasets/use-dataset-schema";
import { useEdaWorkspace, useGenerateOverview, useWorkspaceQuestions } from "@/features/eda/use-eda";

import { EdaAssistPanel } from "./eda-assist-panel";
import { EdaFindingsPanel } from "./eda-findings-panel";
import { EdaOverviewPanel } from "./eda-overview-panel";

export function EdaWorkspace({ workspaceId }: { workspaceId: string }) {
  const workspaceQuery = useEdaWorkspace(workspaceId);
  const datasetQuery = useDataset(workspaceQuery.data?.dataset_id);
  const schemaQuery = useDatasetSchema(workspaceQuery.data?.dataset_id, workspaceQuery.data?.table_name ?? undefined);
  const questionsQuery = useWorkspaceQuestions(workspaceId);
  const generateOverview = useGenerateOverview(workspaceId);

  if (workspaceQuery.isLoading) return <LoadingState count={1} itemClassName="h-96" />;
  if (workspaceQuery.isError || !workspaceQuery.data) {
    return (
      <ErrorState
        title="Unable to load this EDA workspace"
        retry={() => void workspaceQuery.refetch()}
      />
    );
  }

  const workspace = workspaceQuery.data;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[16rem_1fr]">
      <aside className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <div>
          <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Dataset</p>
          <p className="text-sm font-medium text-foreground">{datasetQuery.data?.name ?? "…"}</p>
        </div>
        {workspace.table_name ? (
          <div>
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Table</p>
            <p className="font-mono text-sm text-foreground">{workspace.table_name}</p>
          </div>
        ) : null}
        <div>
          <p className="mb-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Columns</p>
          {schemaQuery.data?.[0] ? (
            <ul className="flex flex-col gap-1">
              {schemaQuery.data[0].columns.map((c) => (
                <li key={c.column_name} className="flex items-center justify-between text-xs">
                  <span className="truncate text-foreground">{c.column_name}</span>
                  <Badge variant="outline" className="shrink-0 text-[10px]">
                    {c.data_type}
                  </Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-muted-foreground">Loading…</p>
          )}
        </div>
      </aside>

      <div className="flex flex-col gap-5">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">{workspace.name}</h2>
          <Button size="sm" onClick={() => generateOverview.mutate()} disabled={generateOverview.isPending}>
            <Sparkles className="size-4" aria-hidden="true" />
            {generateOverview.isPending ? "Generating…" : "Generate EDA Overview"}
          </Button>
        </div>

        <EdaAssistPanel datasetId={workspace.dataset_id} tableName={workspace.table_name ?? undefined} />

        {workspace.overview ? (
          <EdaOverviewPanel overview={workspace.overview} />
        ) : (
          <div className="rounded-xl border border-dashed border-border bg-card/50 px-6 py-10 text-center text-sm text-muted-foreground">
            Click &ldquo;Generate EDA Overview&rdquo; for a deterministic statistical summary — missingness, distributions,
            correlations, date trends, and outliers.
          </div>
        )}

        <div className="rounded-xl border border-border bg-card p-4">
          <p className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-foreground">
            <HelpCircle className="size-4" aria-hidden="true" />
            Questions to explore
          </p>
          {questionsQuery.data && questionsQuery.data.length > 0 ? (
            <ul className="flex flex-col gap-1.5">
              {questionsQuery.data.map((q, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <Badge variant="outline" className="mt-0.5 shrink-0">
                    {q.category}
                  </Badge>
                  <span className="text-foreground">{q.question}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              Generate an overview first, or questions will appear here automatically once this table is profiled.
            </p>
          )}
        </div>

        <div className="rounded-xl border border-border bg-card p-4">
          <p className="mb-3 text-sm font-semibold text-foreground">Findings</p>
          <EdaFindingsPanel workspaceId={workspaceId} findings={workspace.findings} />
        </div>
      </div>
    </div>
  );
}
