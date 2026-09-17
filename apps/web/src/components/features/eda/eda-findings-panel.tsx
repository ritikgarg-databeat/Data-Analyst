"use client";

import { useState } from "react";
import { Lightbulb, Trash2 } from "lucide-react";
import type { EdaFindingSchema } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useAddFinding, useDeleteFinding } from "@/features/eda/use-eda";

/** Structured EDA findings (section 51 of the Phase 5 spec) — observation -> evidence -> implication -> action. */
export function EdaFindingsPanel({ workspaceId, findings }: { workspaceId: string; findings: EdaFindingSchema[] }) {
  const addMutation = useAddFinding(workspaceId);
  const deleteMutation = useDeleteFinding(workspaceId);
  const [expanded, setExpanded] = useState(false);
  const [observation, setObservation] = useState("");
  const [evidence, setEvidence] = useState("");
  const [businessImplication, setBusinessImplication] = useState("");
  const [recommendedAction, setRecommendedAction] = useState("");

  function reset() {
    setObservation("");
    setEvidence("");
    setBusinessImplication("");
    setRecommendedAction("");
    setExpanded(false);
  }

  function handleAdd() {
    if (!observation.trim()) return;
    addMutation.mutate(
      {
        observation: observation.trim(),
        evidence: evidence.trim() || undefined,
        business_implication: businessImplication.trim() || undefined,
        recommended_action: recommendedAction.trim() || undefined,
      },
      { onSuccess: reset },
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {!expanded ? (
        <Button variant="outline" size="sm" className="self-start" onClick={() => setExpanded(true)}>
          <Lightbulb className="size-4" aria-hidden="true" />
          Add Finding
        </Button>
      ) : (
        <div className="flex flex-col gap-2 rounded-lg border border-border p-3">
          <label className="text-xs font-medium text-muted-foreground">Observation</label>
          <Input value={observation} onChange={(e) => setObservation(e.target.value)} placeholder="Revenue increased 18% YoY." />
          <label className="text-xs font-medium text-muted-foreground">Evidence</label>
          <Textarea
            value={evidence}
            onChange={(e) => setEvidence(e.target.value)}
            placeholder="Growth was primarily driven by enterprise customers."
            className="min-h-16"
          />
          <label className="text-xs font-medium text-muted-foreground">Business implication</label>
          <Textarea
            value={businessImplication}
            onChange={(e) => setBusinessImplication(e.target.value)}
            className="min-h-16"
          />
          <label className="text-xs font-medium text-muted-foreground">Recommended action</label>
          <Textarea
            value={recommendedAction}
            onChange={(e) => setRecommendedAction(e.target.value)}
            className="min-h-16"
          />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={reset}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleAdd} disabled={!observation.trim() || addMutation.isPending}>
              Save Finding
            </Button>
          </div>
        </div>
      )}

      {findings.length === 0 ? (
        <EmptyState
          icon={Lightbulb}
          title="No findings yet"
          description="Capture what you learn as structured findings — they'll feed into future case studies and projects."
        />
      ) : (
        <ul className="flex flex-col gap-2">
          {findings.map((f) => (
            <li key={f.id} className="rounded-lg border border-border p-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-foreground">{f.observation}</p>
                <button
                  type="button"
                  onClick={() => deleteMutation.mutate(f.id)}
                  aria-label="Delete finding"
                  className="shrink-0 rounded p-1 text-muted-foreground hover:text-destructive"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
              {f.evidence ? <p className="mt-1 text-sm text-muted-foreground">Evidence: {f.evidence}</p> : null}
              {f.business_implication ? (
                <p className="mt-1 text-sm text-muted-foreground">Implication: {f.business_implication}</p>
              ) : null}
              {f.recommended_action ? (
                <p className="mt-1 text-sm text-muted-foreground">Action: {f.recommended_action}</p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
