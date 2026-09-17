"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Boxes, Plus, Trash2 } from "lucide-react";
import type { DataModelKind } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCreateDataModel, useDataModels, useDeleteDataModel } from "@/features/data-modeling/use-data-models";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

interface ModelListPageProps {
  modelKind: DataModelKind;
  basePath: string; // e.g. "/data-modeler", "/architecture", "/pipeline"
  emptyDescription: string;
}

/** Shared list/create/delete view for the Data Modeler, Architecture Diagram Builder, and Pipeline
 * Playground — they differ only in `modelKind` and the canvas's node-type palette. */
export function ModelListPage({ modelKind, basePath, emptyDescription }: ModelListPageProps) {
  const router = useRouter();
  const modelsQuery = useDataModels(modelKind);
  const createModel = useCreateDataModel(modelKind);
  const deleteModel = useDeleteDataModel(modelKind);
  const [name, setName] = useState("");

  function handleCreate() {
    if (!name.trim()) return;
    createModel.mutate({ name: name.trim() }, { onSuccess: (model) => router.push(`${basePath}/${model.id}`) });
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-xl border border-border bg-card p-4">
        <p className="mb-3 text-sm font-semibold text-foreground">Start a new model</p>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Ecommerce Star Schema"
            className="w-64"
            onKeyDown={(event) => event.key === "Enter" && handleCreate()}
          />
          <Button onClick={handleCreate} disabled={!name.trim() || createModel.isPending}>
            <Plus className="size-4" aria-hidden="true" />
            Create
          </Button>
        </div>
      </div>

      <div>
        <p className="mb-3 text-sm font-semibold text-foreground">Your models</p>
        {modelsQuery.isLoading ? (
          <LoadingState count={3} itemClassName="h-16" />
        ) : modelsQuery.isError ? (
          <ErrorState retry={() => void modelsQuery.refetch()} />
        ) : !modelsQuery.data || modelsQuery.data.length === 0 ? (
          <EmptyState icon={Boxes} title="No models yet" description={emptyDescription} />
        ) : (
          <ul className="flex flex-col gap-2">
            {modelsQuery.data.map((model) => (
              <li key={model.id} className="flex items-center gap-2 rounded-lg border border-border p-3">
                <button
                  type="button"
                  onClick={() => router.push(`${basePath}/${model.id}`)}
                  className="flex-1 text-left"
                >
                  <span className="block text-sm font-medium text-foreground">{model.name}</span>
                  <span className="text-xs text-muted-foreground">
                    {model.description ? `${model.description} · ` : ""}updated {formatDate(model.updated_at)}
                  </span>
                </button>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Delete ${model.name}`}
                  onClick={() => deleteModel.mutate(model.id)}
                  disabled={deleteModel.isPending}
                >
                  <Trash2 className="size-4 text-muted-foreground" aria-hidden="true" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
