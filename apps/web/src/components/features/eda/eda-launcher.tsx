"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Microscope, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Select } from "@/components/ui/select";
import { useDatasets } from "@/features/datasets/use-datasets";
import { useCreateEdaWorkspace, useEdaWorkspaces } from "@/features/eda/use-eda";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

/** The /eda landing view: pick a dataset to start a new EDA workspace, or reopen a saved one. */
export function EdaLauncher() {
  const router = useRouter();
  const workspacesQuery = useEdaWorkspaces();
  const datasetsQuery = useDatasets();
  const createWorkspace = useCreateEdaWorkspace();
  const [selectedDataset, setSelectedDataset] = useState("");

  const readyDatasets = (datasetsQuery.data ?? []).filter((d) => d.status === "READY" && d.tables.length > 0);

  function handleStart() {
    const dataset = readyDatasets.find((d) => d.id === selectedDataset);
    if (!dataset) return;
    createWorkspace.mutate(
      { dataset_id: dataset.id, name: `${dataset.name} exploration` },
      { onSuccess: (workspace) => router.push(`/eda/${workspace.id}`) },
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="mb-3 text-sm font-semibold text-foreground">Start a new EDA workspace</p>
        {datasetsQuery.isLoading ? (
          <LoadingState count={1} itemClassName="h-10" />
        ) : datasetsQuery.isError ? (
          <ErrorState
            title="Unable to load datasets"
            message="We couldn't reach the API to load your datasets."
            retry={() => void datasetsQuery.refetch()}
          />
        ) : readyDatasets.length === 0 ? (
          <p className="text-sm text-muted-foreground">Import a dataset first, then come back here to explore it.</p>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <Select value={selectedDataset} onChange={(e) => setSelectedDataset(e.target.value)} className="w-64">
              <option value="">Choose a dataset…</option>
              {readyDatasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
            <Button onClick={handleStart} disabled={!selectedDataset || createWorkspace.isPending}>
              <Plus className="size-4" aria-hidden="true" />
              Start Exploring
            </Button>
          </div>
        )}
      </div>

      <div>
        <p className="mb-3 text-sm font-semibold text-foreground">Your EDA workspaces</p>
        {workspacesQuery.isLoading ? (
          <LoadingState count={3} itemClassName="h-16" />
        ) : workspacesQuery.isError ? (
          <ErrorState retry={() => void workspacesQuery.refetch()} />
        ) : !workspacesQuery.data || workspacesQuery.data.length === 0 ? (
          <EmptyState
            icon={Microscope}
            title="No EDA workspaces yet"
            description="Start one above to combine schema, statistics, charts, and notes for a dataset in one place."
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {workspacesQuery.data.map((workspace) => (
              <li key={workspace.id}>
                <button
                  type="button"
                  onClick={() => router.push(`/eda/${workspace.id}`)}
                  className="flex w-full items-center justify-between gap-2 rounded-lg border border-border p-3 text-left hover:bg-accent/40"
                >
                  <span>
                    <span className="block text-sm font-medium text-foreground">{workspace.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {workspace.findings.length} finding(s) · updated {formatDate(workspace.updated_at)}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
