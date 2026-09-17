"use client";

import { useState } from "react";
import type { CaseAttempt, RecommendationPayload } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useSaveRecommendation } from "@/features/case-studies/use-case-studies";

const EMPTY: RecommendationPayload = {
  recommendation: "",
  why: "",
  expected_impact: "",
  risks: "",
  implementation_considerations: "",
  next_steps: "",
};

const FIELDS: Array<{ key: keyof RecommendationPayload; label: string; placeholder: string }> = [
  { key: "recommendation", label: "Recommendation", placeholder: "What should the business do?" },
  { key: "why", label: "Why", placeholder: "What evidence supports this?" },
  { key: "expected_impact", label: "Expected Impact", placeholder: "What's the expected effect, quantified if possible?" },
  { key: "risks", label: "Risks", placeholder: "What could go wrong, or what does this recommendation depend on?" },
  { key: "implementation_considerations", label: "Implementation Considerations", placeholder: "Who needs to be involved, and what's needed to execute?" },
  { key: "next_steps", label: "Next Steps", placeholder: "What's the immediate next action?" },
];

/** Recommend (spec section 19) — Recommendation/Why/Expected Impact/Risks/
 * Implementation Considerations/Next Steps, saved as one object per blur.
 * Local, controlled state (see CaseFrameTab's docstring for why — avoids
 * losing an earlier field's edit to a race with a later field's blur). */
export function CaseRecommendTab({ attempt }: { attempt: CaseAttempt }) {
  const saveRecommendation = useSaveRecommendation(attempt.id);
  // Local, controlled state — see CaseFrameTab's docstring for why there's
  // no reset-on-prop-change effect (the workspace remounts per attempt).
  const [recommendation, setRecommendation] = useState<RecommendationPayload>(attempt.recommendation ?? EMPTY);

  function handleBlur(key: keyof RecommendationPayload, value: string) {
    setRecommendation((prev) => {
      const next = { ...prev, [key]: value };
      saveRecommendation.mutate(next);
      return next;
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Business Recommendation</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {FIELDS.map((field) => (
          <div key={field.key} className="flex flex-col gap-1">
            <Label htmlFor={`recommend-${field.key}`}>{field.label}</Label>
            <Textarea
              id={`recommend-${field.key}`}
              value={recommendation[field.key]}
              onChange={(event) => setRecommendation((prev) => ({ ...prev, [field.key]: event.target.value }))}
              onBlur={(event) => handleBlur(field.key, event.target.value)}
              rows={2}
              placeholder={field.placeholder}
            />
          </div>
        ))}
        {saveRecommendation.isError ? (
          <p className="text-xs text-destructive">Couldn&apos;t save — check your connection and try again.</p>
        ) : null}
      </CardContent>
    </Card>
  );
}
