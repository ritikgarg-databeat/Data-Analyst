"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { FindingConfidence } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { EvidenceList } from "@/components/features/findings/evidence-list";
import {
  useAddFindingEvidence,
  useCreateFinding,
  useDeleteEvidence,
  useDeleteFinding,
  useFindings,
  useUpdateFinding,
  type FindingOwner,
} from "@/features/findings/use-findings";

const CONFIDENCE_VARIANT: Record<FindingConfidence, "success" | "warning" | "outline"> = {
  HIGH: "success",
  MEDIUM: "warning",
  LOW: "outline",
};

/**
 * Findings (spec sections 15-16) — structured Observation/Evidence/Impact/
 * Confidence records a learner builds up during analysis. Shared between the
 * Case Workspace and the Project Workspace via `owner` (exactly one of
 * `caseAttemptId`/`projectId`, matching the backend's Finding model).
 */
export function FindingsPanel({ owner }: { owner: FindingOwner }) {
  const findingsQuery = useFindings(owner);
  const createFinding = useCreateFinding(owner);
  const updateFinding = useUpdateFinding(owner);
  const deleteFinding = useDeleteFinding(owner);
  const addEvidence = useAddFindingEvidence(owner);
  const deleteEvidence = useDeleteEvidence(owner);

  const [observation, setObservation] = useState("");

  const submit = () => {
    if (!observation.trim()) return;
    createFinding.mutate({ observation: observation.trim() });
    setObservation("");
  };

  const findings = findingsQuery.data ?? [];

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 rounded-lg border border-border bg-card p-3">
        <Textarea
          value={observation}
          onChange={(e) => setObservation(e.target.value)}
          placeholder="What did you observe in the data? (e.g. Region X's revenue declined 40% while other regions were flat.)"
          rows={2}
        />
        <Button type="button" size="sm" onClick={submit} disabled={createFinding.isPending} className="self-start">
          <Plus className="size-4" aria-hidden="true" />
          Add finding
        </Button>
      </div>

      {findingsQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading findings...</p>
      ) : findings.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No findings yet — record what you notice in the data as you go, with evidence to back it up.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {findings.map((finding) => (
            <li key={finding.id} className="rounded-lg border border-border bg-card p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-foreground">{finding.observation}</p>
                <button
                  type="button"
                  onClick={() => deleteFinding.mutate(finding.id)}
                  className="shrink-0 text-muted-foreground hover:text-destructive"
                  aria-label="Delete finding"
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </button>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Select
                  value={finding.confidence ?? ""}
                  onChange={(e) =>
                    updateFinding.mutate({
                      findingId: finding.id,
                      payload: { confidence: (e.target.value || undefined) as FindingConfidence | undefined },
                    })
                  }
                  className="h-7 w-32 text-xs"
                >
                  <option value="">Confidence</option>
                  <option value="LOW">Low confidence</option>
                  <option value="MEDIUM">Medium confidence</option>
                  <option value="HIGH">High confidence</option>
                </Select>
                {finding.confidence ? (
                  <Badge variant={CONFIDENCE_VARIANT[finding.confidence]}>{finding.confidence}</Badge>
                ) : null}
              </div>

              <Textarea
                defaultValue={finding.impact ?? ""}
                onBlur={(e) => {
                  if (e.target.value !== (finding.impact ?? "")) {
                    updateFinding.mutate({ findingId: finding.id, payload: { impact: e.target.value } });
                  }
                }}
                placeholder="Why does this matter to the business? (impact)"
                rows={2}
                className="mt-2 text-xs"
              />

              <EvidenceList
                evidence={finding.evidence}
                adding={addEvidence.isPending}
                onAdd={(payload) => addEvidence.mutate({ findingId: finding.id, payload })}
                onDelete={(evidenceId) => deleteEvidence.mutate(evidenceId)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
