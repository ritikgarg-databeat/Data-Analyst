"use client";

import { useState } from "react";
import type { CaseAttempt, ProblemFramingPayload } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useSaveFraming } from "@/features/case-studies/use-case-studies";

const EMPTY_FRAMING: ProblemFramingPayload = {
  problem: "",
  objective: "",
  primary_metric: "",
  scope: "",
  hypotheses: "",
};

const FIELDS: Array<{ key: keyof ProblemFramingPayload; label: string; placeholder: string }> = [
  { key: "problem", label: "Problem", placeholder: "State the problem precisely, in your own words." },
  { key: "objective", label: "Objective", placeholder: "What are you trying to determine or achieve?" },
  { key: "primary_metric", label: "Primary Metric", placeholder: "The single metric this analysis centers on." },
  { key: "scope", label: "Scope", placeholder: "What's in scope (time range, segment, etc.) and what's out of scope?" },
  { key: "hypotheses", label: "Hypotheses", placeholder: "What do you think might explain this, before digging in?" },
];

/**
 * Frame (spec section 9) — Problem/Objective/Primary Metric/Scope/Hypotheses,
 * saved as one object on each field's blur (no per-field endpoint). Kept as
 * local, controlled state (not read from `attempt` at blur time) so tabbing
 * through several fields quickly doesn't lose earlier edits to a race
 * between each field's own save request and the next field's blur — each
 * blur's payload is built from the latest local state, not a stale closure.
 */
export function CaseFrameTab({ attempt }: { attempt: CaseAttempt }) {
  const saveFraming = useSaveFraming(attempt.id);
  // Local, controlled state — initialized once from the attempt this
  // component is mounted for (the Case Workspace re-mounts per attempt via
  // routing, so there's no need to re-sync this on every attempt refetch,
  // which would risk clobbering an in-flight local edit).
  const [framing, setFraming] = useState<ProblemFramingPayload>(attempt.problem_framing ?? EMPTY_FRAMING);

  function handleBlur(key: keyof ProblemFramingPayload, value: string) {
    setFraming((prev) => {
      const next = { ...prev, [key]: value };
      saveFraming.mutate(next);
      return next;
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Problem Framing</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {FIELDS.map((field) => (
          <div key={field.key} className="flex flex-col gap-1">
            <Label htmlFor={`frame-${field.key}`}>{field.label}</Label>
            <Textarea
              id={`frame-${field.key}`}
              value={framing[field.key]}
              onChange={(event) => setFraming((prev) => ({ ...prev, [field.key]: event.target.value }))}
              onBlur={(event) => handleBlur(field.key, event.target.value)}
              rows={2}
              placeholder={field.placeholder}
            />
          </div>
        ))}
        {saveFraming.isError ? (
          <p className="text-xs text-destructive">Couldn&apos;t save — check your connection and try again.</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
