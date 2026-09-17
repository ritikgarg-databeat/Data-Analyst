"use client";

import type { CaseAttempt } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useSaveClarification } from "@/features/case-studies/use-case-studies";

/**
 * Clarify (spec section 8) — free-text clarifying questions, evaluated
 * loosely by the rubric ("Problem Framing" criteria), not exact-wording
 * matched. This is where the learner should ask what a real analyst would
 * ask before touching any data.
 */
export function CaseClarifyTab({ attempt }: { attempt: CaseAttempt }) {
  const saveClarification = useSaveClarification(attempt.id);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Clarifying Questions</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <p className="text-sm text-muted-foreground">
          What would you ask the stakeholder before starting the analysis? Think about metric definitions, scope,
          timeframe, success criteria, and assumptions.
        </p>
        <Textarea
          defaultValue={attempt.clarification_questions ?? ""}
          onBlur={(event) => {
            if (event.target.value !== (attempt.clarification_questions ?? "")) {
              saveClarification.mutate(event.target.value);
            }
          }}
          rows={6}
          placeholder="e.g. Which specific metric are we talking about, and over what time window? Has anything else changed recently that could explain this?"
        />
        {saveClarification.isError ? (
          <p className="text-xs text-destructive">Couldn&apos;t save — check your connection and try again.</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
