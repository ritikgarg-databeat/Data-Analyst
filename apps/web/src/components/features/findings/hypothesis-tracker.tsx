"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { HypothesisStatus } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { EvidenceList } from "@/components/features/findings/evidence-list";
import {
  useAddHypothesisEvidence,
  useCreateHypothesis,
  useDeleteEvidence,
  useDeleteHypothesis,
  useHypotheses,
  useUpdateHypothesis,
  type FindingOwner,
} from "@/features/findings/use-findings";

const STATUS_LABELS: Record<HypothesisStatus, string> = {
  UNCHECKED: "Unchecked",
  INVESTIGATING: "Investigating",
  SUPPORTED: "Supported",
  REJECTED: "Rejected",
  INCONCLUSIVE: "Inconclusive",
};

const STATUS_VARIANT: Record<HypothesisStatus, "outline" | "warning" | "success" | "destructive" | "secondary"> = {
  UNCHECKED: "outline",
  INVESTIGATING: "warning",
  SUPPORTED: "success",
  REJECTED: "destructive",
  INCONCLUSIVE: "secondary",
};

/**
 * Hypothesis Tracker (spec section 17) — H1/H2/H3-style tracked hypotheses
 * with a status (Unchecked/Investigating/Supported/Rejected/Inconclusive)
 * and evidence. Shared between the Case Workspace and the Project Workspace.
 */
export function HypothesisTracker({ owner }: { owner: FindingOwner }) {
  const hypothesesQuery = useHypotheses(owner);
  const createHypothesis = useCreateHypothesis(owner);
  const updateHypothesis = useUpdateHypothesis(owner);
  const deleteHypothesis = useDeleteHypothesis(owner);
  const addEvidence = useAddHypothesisEvidence(owner);
  const deleteEvidence = useDeleteEvidence(owner);

  const [statement, setStatement] = useState("");

  const submit = () => {
    if (!statement.trim()) return;
    createHypothesis.mutate({ statement: statement.trim() });
    setStatement("");
  };

  const hypotheses = hypothesesQuery.data ?? [];

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <Input
          value={statement}
          onChange={(e) => setStatement(e.target.value)}
          placeholder="Hypothesis, e.g. H1: The decline is concentrated in one region"
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <Button type="button" size="sm" onClick={submit} disabled={createHypothesis.isPending}>
          <Plus className="size-4" aria-hidden="true" />
          Add
        </Button>
      </div>

      {hypothesesQuery.isLoading ? (
        <p className="text-sm text-muted-foreground">Loading hypotheses...</p>
      ) : hypotheses.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No hypotheses yet — write down what you think might explain the problem, then check each one against
          the data.
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {hypotheses.map((hypothesis, index) => (
            <li key={hypothesis.id} className="rounded-lg border border-border bg-card p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-foreground">
                  <span className="font-medium">H{index + 1}:</span> {hypothesis.statement}
                </p>
                <button
                  type="button"
                  onClick={() => deleteHypothesis.mutate(hypothesis.id)}
                  className="shrink-0 text-muted-foreground hover:text-destructive"
                  aria-label="Delete hypothesis"
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                </button>
              </div>

              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Select
                  value={hypothesis.status}
                  onChange={(e) =>
                    updateHypothesis.mutate({
                      hypothesisId: hypothesis.id,
                      payload: { status: e.target.value as HypothesisStatus },
                    })
                  }
                  className="h-7 w-36 text-xs"
                >
                  {Object.entries(STATUS_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
                <Badge variant={STATUS_VARIANT[hypothesis.status]}>{STATUS_LABELS[hypothesis.status]}</Badge>
              </div>

              <EvidenceList
                evidence={hypothesis.evidence}
                adding={addEvidence.isPending}
                onAdd={(payload) => addEvidence.mutate({ hypothesisId: hypothesis.id, payload })}
                onDelete={(evidenceId) => deleteEvidence.mutate(evidenceId)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
