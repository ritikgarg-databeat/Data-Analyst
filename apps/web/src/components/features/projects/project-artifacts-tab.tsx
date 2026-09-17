"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { Project, ProjectArtifactType } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCreateProjectArtifact, useDeleteProjectArtifact } from "@/features/projects/use-projects";

import { ARTIFACT_TYPE_LABELS, ARTIFACT_TYPES } from "./project-format";

/** Artifacts — snapshots of work done elsewhere (a saved SQL query, a Python
 * execution, a chart, a data model, a dbt model, or a free-text note) that a
 * learner links back into the project as evidence of what they built. */
export function ProjectArtifactsTab({ project }: { project: Project }) {
  const createArtifact = useCreateProjectArtifact(project.id);
  const deleteArtifact = useDeleteProjectArtifact(project.id);

  const [artifactType, setArtifactType] = useState<ProjectArtifactType>("NOTE");
  const [label, setLabel] = useState("");
  const [refId, setRefId] = useState("");
  const [snapshot, setSnapshot] = useState("");
  const [notes, setNotes] = useState("");

  function handleAdd() {
    if (!label.trim()) return;
    createArtifact.mutate(
      {
        artifact_type: artifactType,
        label: label.trim(),
        ref_id: refId.trim() || undefined,
        snapshot: snapshot.trim() || undefined,
        notes: notes.trim() || undefined,
      },
      {
        onSuccess: () => {
          setLabel("");
          setRefId("");
          setSnapshot("");
          setNotes("");
        },
      },
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">Add an artifact</p>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <Select value={artifactType} onChange={(event) => setArtifactType(event.target.value as ProjectArtifactType)}>
            {ARTIFACT_TYPES.map((type) => (
              <option key={type} value={type}>
                {ARTIFACT_TYPE_LABELS[type]}
              </option>
            ))}
          </Select>
          <Input value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Label (required)" />
          <Input
            value={refId}
            onChange={(event) => setRefId(event.target.value)}
            placeholder="Reference id (optional, e.g. saved query id)"
          />
          <Input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Notes (optional)" />
        </div>
        <Textarea
          value={snapshot}
          onChange={(event) => setSnapshot(event.target.value)}
          placeholder="Snapshot (optional) — paste the query, code, or a summary of what this artifact captures"
          rows={3}
        />
        <Button size="sm" onClick={handleAdd} disabled={!label.trim() || createArtifact.isPending} className="self-start">
          <Plus className="size-4" aria-hidden="true" />
          Add artifact
        </Button>
      </div>

      {project.artifacts.length === 0 ? (
        <p className="text-sm text-muted-foreground">No artifacts yet — link a saved query, script, chart, or note above.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {project.artifacts.map((artifact) => (
            <li key={artifact.id} className="rounded-xl border border-border bg-card p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{ARTIFACT_TYPE_LABELS[artifact.artifact_type]}</Badge>
                    <p className="text-sm font-medium text-foreground">{artifact.label}</p>
                  </div>
                  {artifact.notes ? <p className="mt-1 text-sm text-muted-foreground">{artifact.notes}</p> : null}
                </div>
                <button
                  type="button"
                  onClick={() => deleteArtifact.mutate(artifact.id)}
                  className="shrink-0 text-muted-foreground hover:text-destructive"
                  aria-label={`Delete ${artifact.label}`}
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </button>
              </div>
              {artifact.snapshot ? (
                <pre className="mt-2 overflow-x-auto rounded-md bg-accent/40 p-3 text-xs whitespace-pre-wrap text-foreground">
                  {artifact.snapshot}
                </pre>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
