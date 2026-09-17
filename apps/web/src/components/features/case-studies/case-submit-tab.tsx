"use client";

import { useState } from "react";
import { Check, X } from "lucide-react";
import type {
  Case,
  CaseAttempt,
  CaseFeedback,
  ExecutiveSummaryPayload,
  ReflectionPayload,
  RevealCaseSolutionResponse,
} from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import {
  useRevealCaseSolution,
  useSaveExecutiveSummary,
  useSaveReflection,
  useSubmitCaseAttempt,
} from "@/features/case-studies/use-case-studies";

const EMPTY_SUMMARY: ExecutiveSummaryPayload = {
  problem: "",
  key_findings: "",
  business_impact: "",
  recommendation: "",
  next_steps: "",
};

const SUMMARY_FIELDS: Array<{ key: keyof ExecutiveSummaryPayload; label: string }> = [
  { key: "problem", label: "Problem" },
  { key: "key_findings", label: "Key Findings" },
  { key: "business_impact", label: "Business Impact" },
  { key: "recommendation", label: "Recommendation" },
  { key: "next_steps", label: "Next Steps" },
];

const READINESS_LABELS: Record<keyof CaseAttempt["submission_readiness"], string> = {
  problem_framed: "Problem framed",
  data_understood: "Data understood",
  findings_documented: "Findings documented",
  recommendation_written: "Recommendation written",
  executive_summary_written: "Executive summary written",
};

const FEEDBACK_BUCKETS: Array<{ key: keyof CaseFeedback; label: string }> = [
  { key: "what_went_well", label: "What went well" },
  { key: "what_missed", label: "What was missed" },
  { key: "technical_issues", label: "Technical issues" },
  { key: "business_reasoning_issues", label: "Business reasoning issues" },
  { key: "communication_issues", label: "Communication issues" },
];

const REFLECTION_FIELDS: Array<{ key: keyof ReflectionPayload; label: string }> = [
  { key: "what_learned", label: "What did you learn?" },
  { key: "what_difficult", label: "What was difficult?" },
  { key: "what_differently", label: "What would you do differently?" },
  { key: "skill_improved", label: "What skill did this improve?" },
  { key: "what_review", label: "What should you review?" },
];

/**
 * Communicate & Submit (spec sections 20, 46-47, 55) — the executive
 * summary, a read-only submission-readiness checklist, the rubric
 * self-assessment, the submit action, and (once completed) the real
 * computed score/feedback, a "reveal reference solution" action, and the
 * reflection form.
 */
export function CaseSubmitTab({ caseData, attempt }: { caseData: Case; attempt: CaseAttempt }) {
  const saveSummary = useSaveExecutiveSummary(attempt.id);
  const submitAttempt = useSubmitCaseAttempt(attempt.id);
  const revealSolution = useRevealCaseSolution(attempt.id);
  const saveReflection = useSaveReflection(attempt.id);

  const [selections, setSelections] = useState<Record<string, string[]>>(attempt.rubric_selections ?? {});
  const [solution, setSolution] = useState<RevealCaseSolutionResponse | null>(null);

  // Local, controlled state for both forms below (see CaseFrameTab's
  // docstring for why: reading straight from `attempt` at blur time races
  // against earlier fields' still-in-flight saves when tabbing through
  // several fields quickly, silently dropping edits). Initialized once per
  // mount — the workspace remounts per attempt via routing.
  const [summary, setSummary] = useState<ExecutiveSummaryPayload>(attempt.executive_summary ?? EMPTY_SUMMARY);
  const [reflection, setReflection] = useState<ReflectionPayload>(
    attempt.reflection ?? {
      what_learned: "",
      what_difficult: "",
      what_differently: "",
      skill_improved: "",
      what_review: "",
    },
  );

  const isCompleted = attempt.status === "COMPLETED";

  function handleSummaryBlur(key: keyof ExecutiveSummaryPayload, value: string) {
    setSummary((prev) => {
      const next = { ...prev, [key]: value };
      saveSummary.mutate(next);
      return next;
    });
  }

  function toggleCriterion(category: string, criterion: string, checked: boolean) {
    setSelections((prev) => {
      const current = new Set(prev[category] ?? []);
      if (checked) current.add(criterion);
      else current.delete(criterion);
      return { ...prev, [category]: Array.from(current) };
    });
  }

  function handleReflectionBlur(key: keyof ReflectionPayload, value: string) {
    setReflection((prev) => {
      const next = { ...prev, [key]: value };
      saveReflection.mutate(next);
      return next;
    });
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Executive Summary</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {SUMMARY_FIELDS.map((field) => (
            <div key={field.key} className="flex flex-col gap-1">
              <Label htmlFor={`summary-${field.key}`}>{field.label}</Label>
              <Textarea
                id={`summary-${field.key}`}
                value={summary[field.key]}
                onChange={(event) => setSummary((prev) => ({ ...prev, [field.key]: event.target.value }))}
                onBlur={(event) => handleSummaryBlur(field.key, event.target.value)}
                rows={2}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Submission Readiness</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="grid grid-cols-1 gap-1.5 text-sm sm:grid-cols-2">
            {(Object.keys(READINESS_LABELS) as Array<keyof CaseAttempt["submission_readiness"]>).map((key) => {
              const ready = attempt.submission_readiness[key];
              return (
                <li key={key} className="flex items-center gap-2">
                  {ready ? (
                    <Check className="size-4 text-success" aria-hidden="true" />
                  ) : (
                    <X className="size-4 text-muted-foreground" aria-hidden="true" />
                  )}
                  <span className={ready ? "text-foreground" : "text-muted-foreground"}>{READINESS_LABELS[key]}</span>
                </li>
              );
            })}
          </ul>
        </CardContent>
      </Card>

      {!isCompleted ? (
        <>
          {caseData.rubric.map((category) => (
            <Card key={category.category}>
              <CardHeader>
                <CardTitle>
                  {category.category} <span className="font-normal text-muted-foreground">({category.weight}%)</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="flex flex-col gap-2">
                  {category.criteria.map((criterion) => (
                    <li key={criterion.criterion}>
                      <label className="flex cursor-pointer items-start gap-2 text-sm">
                        <input
                          type="checkbox"
                          className="mt-0.5 size-4"
                          checked={(selections[category.category] ?? []).includes(criterion.criterion)}
                          onChange={(event) =>
                            toggleCriterion(category.category, criterion.criterion, event.target.checked)
                          }
                        />
                        <span className="text-foreground">{criterion.criterion}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}

          <Button
            onClick={() => submitAttempt.mutate(selections)}
            disabled={submitAttempt.isPending}
            className="self-start"
          >
            {submitAttempt.isPending ? "Submitting..." : "Submit case"}
          </Button>
          {submitAttempt.isError ? (
            <p className="text-xs text-destructive">Couldn&apos;t submit — check your connection and try again.</p>
          ) : null}
        </>
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Score: {attempt.score!.overall.toFixed(1)}%</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-col gap-3">
                {attempt.score!.categories.map((cat) => (
                  <div key={cat.category}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-foreground">{cat.category}</span>
                      <span className="text-muted-foreground">{cat.pct.toFixed(0)}%</span>
                    </div>
                    <Progress value={cat.pct} />
                  </div>
                ))}
              </div>

              {attempt.feedback ? (
                <div className="flex flex-col gap-3 text-sm">
                  {FEEDBACK_BUCKETS.map(({ key, label }) => {
                    const items = attempt.feedback![key];
                    if (!items || items.length === 0) return null;
                    return (
                      <div key={key}>
                        <p className="font-medium text-foreground">{label}</p>
                        <ul className="list-inside list-disc text-muted-foreground">
                          {items.map((item, index) => (
                            <li key={index}>{item}</li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Reference Solution</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {!attempt.solution_revealed && !solution ? (
                <Button
                  variant="outline"
                  size="sm"
                  className="self-start"
                  onClick={() => revealSolution.mutate(undefined, { onSuccess: (result) => setSolution(result) })}
                  disabled={revealSolution.isPending}
                >
                  Reveal reference solution
                </Button>
              ) : solution ? (
                <div className="flex flex-col gap-2 text-sm text-foreground">
                  <p>{solution.summary}</p>
                  {solution.key_insights.length > 0 ? (
                    <div>
                      <p className="font-medium">Key insights</p>
                      <ul className="list-inside list-disc text-muted-foreground">
                        {solution.key_insights.map((insight, index) => (
                          <li key={index}>{insight}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {solution.recommendation ? (
                    <p>
                      <span className="font-medium">Recommendation: </span>
                      {solution.recommendation}
                    </p>
                  ) : null}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Click below to reveal the reference solution.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Reflection</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {REFLECTION_FIELDS.map((field) => (
                <div key={field.key} className="flex flex-col gap-1">
                  <Label htmlFor={`reflection-${field.key}`}>{field.label}</Label>
                  <Textarea
                    id={`reflection-${field.key}`}
                    value={reflection[field.key]}
                    onChange={(event) => setReflection((prev) => ({ ...prev, [field.key]: event.target.value }))}
                    onBlur={(event) => handleReflectionBlur(field.key, event.target.value)}
                    rows={2}
                  />
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
