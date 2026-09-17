"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { Project } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useDatasets } from "@/features/datasets/use-datasets";
import { useAddProjectDataset, useDeleteProjectDataset } from "@/features/projects/use-projects";

/** Datasets attached to this project — a project can pull in more than one
 * dataset as the analysis grows, each with a short reason for why it's here. */
export function ProjectDatasetsTab({ project }: { project: Project }) {
  const datasetsQuery = useDatasets();
  const addDataset = useAddProjectDataset(project.id);
  const deleteDataset = useDeleteProjectDataset(project.id);

  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [reason, setReason] = useState("");

  const availableDatasets = (datasetsQuery.data ?? []).filter(
    (dataset) => !project.project_datasets.some((pd) => pd.dataset_id === dataset.id),
  );

  function handleAdd() {
    if (!selectedDatasetId) return;
    addDataset.mutate(
      { dataset_id: selectedDatasetId, reason: reason.trim() || undefined },
      {
        onSuccess: () => {
          setSelectedDatasetId("");
          setReason("");
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="mb-2 text-sm font-semibold text-foreground">Add a dataset</p>
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={selectedDatasetId}
            onChange={(event) => setSelectedDatasetId(event.target.value)}
            className="w-56"
          >
            <option value="">Select a dataset…</option>
            {availableDatasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name}
              </option>
            ))}
          </Select>
          <Input
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Why does this project need it? (optional)"
            className="w-64"
          />
          <Button size="sm" onClick={handleAdd} disabled={!selectedDatasetId || addDataset.isPending}>
            <Plus className="size-4" aria-hidden="true" />
            Add
          </Button>
        </div>
      </div>

      {project.project_datasets.length === 0 ? (
        <p className="text-sm text-muted-foreground">No datasets attached yet — add one above.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {project.project_datasets.map((projectDataset) => {
            const dataset = datasetsQuery.data?.find((d) => d.id === projectDataset.dataset_id);
            return (
              <li
                key={projectDataset.id}
                className="flex items-start justify-between gap-2 rounded-xl border border-border bg-card p-4"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">{dataset?.name ?? projectDataset.dataset_id}</p>
                  {projectDataset.reason ? (
                    <p className="mt-1 text-sm text-muted-foreground">{projectDataset.reason}</p>
                  ) : null}
                </div>
                <button
                  type="button"
                  onClick={() => deleteDataset.mutate(projectDataset.id)}
                  className="shrink-0 text-muted-foreground hover:text-destructive"
                  aria-label={`Remove ${dataset?.name ?? projectDataset.dataset_id}`}
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
