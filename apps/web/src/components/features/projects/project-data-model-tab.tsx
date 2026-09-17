"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";
import type { Project } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { ErrorState } from "@/components/shared/error-state";
import { Section } from "@/components/shared/section";
import { useDataModels } from "@/features/data-modeling/use-data-models";
import { useLinkProjectDataModel, useUpdateProjectDbtRefs } from "@/features/projects/use-projects";

/** Data Model & dbt — links this project to a saved dimensional model (built
 * in the Data Modeler, a separate feature) and tracks free-text dbt model
 * names referenced by the project's transformation layer. */
export function ProjectDataModelTab({ project }: { project: Project }) {
  const modelsQuery = useDataModels("DIMENSIONAL");
  const linkDataModel = useLinkProjectDataModel(project.id);
  const updateDbtRefs = useUpdateProjectDbtRefs(project.id);
  const [newRef, setNewRef] = useState("");

  function handleAddRef() {
    const trimmed = newRef.trim();
    if (!trimmed || project.dbt_model_refs.includes(trimmed)) return;
    updateDbtRefs.mutate({ dbt_model_refs: [...project.dbt_model_refs, trimmed] });
    setNewRef("");
  }

  function handleRemoveRef(ref: string) {
    updateDbtRefs.mutate({ dbt_model_refs: project.dbt_model_refs.filter((r) => r !== ref) });
  }

  return (
    <div className="flex flex-col gap-6">
      <Section title="Data Model" description="Link the dimensional model you're building for this project in the Data Modeler.">
        <div className="rounded-xl border border-border bg-card p-4">
          {modelsQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading your models…</p>
          ) : modelsQuery.isError ? (
            <ErrorState
              title="Unable to load data models"
              message="We couldn't reach the API to load your saved data models."
              retry={() => void modelsQuery.refetch()}
            />
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <Select
                value={project.data_model_id ?? ""}
                onChange={(event) => linkDataModel.mutate({ data_model_id: event.target.value || null })}
                className="w-64"
                disabled={linkDataModel.isPending}
              >
                <option value="">No data model linked</option>
                {(modelsQuery.data ?? []).map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name}
                  </option>
                ))}
              </Select>
              {project.data_model_id ? (
                <Button variant="outline" size="sm" asChild>
                  <a href={`/data-modeler/${project.data_model_id}`} target="_blank" rel="noopener noreferrer">
                    Open in Data Modeler
                  </a>
                </Button>
              ) : null}
            </div>
          )}
        </div>
      </Section>

      <Section title="dbt Model References" description="Free-text names of the dbt models this project's transformation layer builds on.">
        <div className="rounded-xl border border-border bg-card p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Input
              value={newRef}
              onChange={(event) => setNewRef(event.target.value)}
              placeholder="e.g. fct_orders"
              className="w-56"
              onKeyDown={(event) => event.key === "Enter" && handleAddRef()}
            />
            <Button size="sm" onClick={handleAddRef} disabled={!newRef.trim() || updateDbtRefs.isPending}>
              <Plus className="size-4" aria-hidden="true" />
              Add
            </Button>
          </div>
          {project.dbt_model_refs.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {project.dbt_model_refs.map((ref) => (
                <Badge key={ref} variant="secondary" className="gap-1 pr-1">
                  {ref}
                  <button
                    type="button"
                    onClick={() => handleRemoveRef(ref)}
                    aria-label={`Remove ${ref}`}
                    className="rounded-sm hover:bg-foreground/10"
                  >
                    <X className="size-3" aria-hidden="true" />
                  </button>
                </Badge>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-muted-foreground">No dbt models referenced yet.</p>
          )}
        </div>
      </Section>
    </div>
  );
}
