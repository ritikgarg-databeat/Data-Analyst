"use client";

import { useState } from "react";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useExerciseContent } from "@/features/exercises/use-exercise-content";
import { useSubmitExerciseAttempt } from "@/features/exercises/use-exercise-attempt";
import { useRevealExerciseSolution } from "@/features/exercises/use-exercise-solution";

/** A Business/Product Analytics case (spec sections 33, 44, 46) — a richer-framed
 * Exercise. Submission reuses the standard exercise attempt endpoint; when the
 * exercise has a `rubric`, checked criteria are sent as `rubric_selections` and
 * scored deterministically server-side (see app.services.grading.grade). */
export function CaseDetail({ slug }: { slug: string }) {
  const contentQuery = useExerciseContent(slug);
  const submitMutation = useSubmitExerciseAttempt(slug);
  const solutionMutation = useRevealExerciseSolution(slug);

  const [answer, setAnswer] = useState("");
  const [checked, setChecked] = useState<Set<string>>(new Set());

  if (contentQuery.isLoading) return <LoadingState count={1} itemClassName="h-96" />;
  if (contentQuery.isError || !contentQuery.data) {
    return <ErrorState title="Unable to load this case" retry={() => void contentQuery.refetch()} />;
  }

  const c = contentQuery.data;
  const hasRubric = c.rubric.length > 0;

  function toggleCriterion(criterion: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(criterion)) next.delete(criterion);
      else next.add(criterion);
      return next;
    });
  }

  function handleSubmit() {
    submitMutation.mutate({
      submitted_answer: answer,
      rubric_selections: hasRubric ? Array.from(checked) : undefined,
    });
  }

  const result = submitMutation.data;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[20rem_1fr]">
      <aside className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <Badge variant="secondary">{c.points} pts</Badge>
          <Badge variant="outline">{c.difficulty.toLowerCase()}</Badge>
        </div>
        {c.stakeholder ? (
          <div>
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Stakeholder</p>
            <p className="text-sm text-foreground">{c.stakeholder}</p>
          </div>
        ) : null}
        {c.business_context ? (
          <div>
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Business context</p>
            <p className="text-sm text-foreground">{c.business_context}</p>
          </div>
        ) : null}
        {c.constraints.length > 0 ? (
          <div>
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Constraints</p>
            <ul className="list-inside list-disc text-sm text-muted-foreground">
              {c.constraints.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
        {c.expected_deliverables.length > 0 ? (
          <div>
            <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Expected deliverables</p>
            <ul className="list-inside list-disc text-sm text-muted-foreground">
              {c.expected_deliverables.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </aside>

      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-border bg-card p-4">
          <h1 className="mb-2 text-lg font-semibold text-foreground">{c.title}</h1>
          <p className="whitespace-pre-line text-sm text-foreground">{c.prompt}</p>
        </div>

        {hasRubric ? (
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="mb-2 text-sm font-semibold text-foreground">Your answer will be evaluated on</p>
            <p className="mb-2 text-xs text-muted-foreground">
              Write your answer below, then check off which of these your own answer actually covers —
              this is evaluation guidance, not the solution.
            </p>
            <ul className="flex flex-col gap-1.5">
              {c.rubric.map((criterion) => (
                <li key={criterion.criterion} className="flex items-start gap-2 text-sm">
                  <input
                    type="checkbox"
                    id={`rubric-${criterion.criterion}`}
                    checked={checked.has(criterion.criterion)}
                    onChange={() => toggleCriterion(criterion.criterion)}
                    className="mt-1"
                  />
                  <label htmlFor={`rubric-${criterion.criterion}`} className="text-foreground">
                    {criterion.criterion} <span className="text-xs text-muted-foreground">({criterion.points} pts)</span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div className="rounded-xl border border-border bg-card p-4">
          <label htmlFor="case-answer" className="mb-1 block text-sm font-medium text-foreground">
            Your answer
          </label>
          <Textarea
            id="case-answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            className="min-h-40"
            placeholder="Walk through your analysis and recommendation…"
          />
          <Button className="mt-3" onClick={handleSubmit} disabled={!answer.trim() || submitMutation.isPending}>
            {submitMutation.isPending ? "Submitting…" : "Submit"}
          </Button>
        </div>

        {result ? (
          <div className="rounded-xl border border-border bg-card p-4">
            <p className="text-sm font-semibold text-foreground">
              {result.attempt.score !== null ? `Score: ${result.attempt.score.toFixed(0)}%` : "Submitted"}
            </p>
            {result.explanation ? <p className="mt-2 text-sm text-foreground">{result.explanation}</p> : null}
            {!solutionMutation.data ? (
              <Button variant="outline" size="sm" className="mt-2" onClick={() => solutionMutation.mutate()}>
                Reveal Model Answer
              </Button>
            ) : (
              <div className="mt-2 rounded-md bg-accent/40 p-3 text-sm whitespace-pre-line text-foreground">
                {solutionMutation.data.solution}
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
