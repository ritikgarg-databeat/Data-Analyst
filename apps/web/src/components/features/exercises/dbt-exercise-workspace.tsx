"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Lightbulb, RotateCcw, XCircle } from "lucide-react";
import type { ExerciseContent, SubmitDbtExerciseResponse } from "@data-analyst-lab/shared";

import { DifficultyBadge } from "@/components/features/curriculum/difficulty-badge";
import { SqlEditor } from "@/components/features/sql-lab/sql-editor";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useDbtExerciseContent } from "@/features/dbt/use-dbt-exercise-content";
import { useSubmitDbtExercise } from "@/features/dbt/use-submit-dbt-exercise";
import { useRevealExerciseHint } from "@/features/exercises/use-exercise-hint";
import { cn } from "@/lib/utils";

interface DbtExerciseWorkspaceProps {
  slug: string;
  exercise: ExerciseContent;
  onRetryRef?: (retry: () => void) => void;
}

function TestOutcomeRow({ outcome }: { outcome: SubmitDbtExerciseResponse["test_outcomes"][number] }) {
  return (
    <li className="flex items-start gap-2 text-xs">
      {outcome.passed ? (
        <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-success" aria-hidden="true" />
      ) : (
        <XCircle className="mt-0.5 size-3.5 shrink-0 text-destructive" aria-hidden="true" />
      )}
      <div className="min-w-0">
        <span className="font-mono font-medium text-foreground">{outcome.name}</span>
        {outcome.message ? <p className="mt-0.5 text-muted-foreground">{outcome.message}</p> : null}
      </div>
    </li>
  );
}

/**
 * dbt-specific exercise body, rendered by `ExerciseInteraction` when
 * `exercise.exercise_type === "DBT"`. "Submit" writes the model's SQL into
 * the real dbt project and runs `dbt build --select <model>` for real — see
 * app/services/dbt_exercise_service.py. There is no separate "Run" preview
 * step; grading itself is the only way to see the model actually build.
 */
export function DbtExerciseWorkspace({ slug, exercise, onRetryRef }: DbtExerciseWorkspaceProps) {
  const contentQuery = useDbtExerciseContent(slug);
  const submitMutation = useSubmitDbtExercise(slug);
  const hintMutation = useRevealExerciseHint(slug);

  const [sql, setSql] = useState("");
  const [revealedHints, setRevealedHints] = useState<string[]>([]);
  const initializedRef = useRef(false);

  useEffect(() => {
    if (!initializedRef.current && contentQuery.data) {
      setSql(contentQuery.data.starter_sql ?? "");
      initializedRef.current = true;
    }
  }, [contentQuery.data]);

  function reset() {
    setSql(contentQuery.data?.starter_sql ?? "");
    setRevealedHints([]);
    submitMutation.reset();
  }
  onRetryRef?.(reset);

  const canSubmit = sql.trim().length > 0 && !submitMutation.isPending;

  function handleSubmit() {
    if (!canSubmit) return;
    submitMutation.mutate({ submitted_sql: sql });
  }

  function handleHint() {
    hintMutation.mutate(undefined, {
      onSuccess: (response) => setRevealedHints((prev) => [...prev, response.hint]),
    });
  }

  const result = submitMutation.data;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">dbt</Badge>
          <DifficultyBadge difficulty={exercise.difficulty} />
          {exercise.skill_slug ? <Badge variant="secondary">{exercise.skill_slug}</Badge> : null}
          <span className="ml-auto text-xs text-muted-foreground">{exercise.points} pts</span>
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{exercise.title}</h1>
        {exercise.description ? (
          <p className="text-sm text-muted-foreground">{exercise.description}</p>
        ) : null}
      </CardHeader>

      <CardContent className="space-y-5">
        <p className="whitespace-pre-line text-sm text-foreground">{exercise.prompt}</p>

        {contentQuery.isLoading ? (
          <LoadingState count={1} itemClassName="h-64" />
        ) : contentQuery.isError || !contentQuery.data ? (
          <ErrorState
            title="Unable to load dbt exercise details"
            message="We couldn't reach the API to load this exercise's starter SQL."
            retry={() => void contentQuery.refetch()}
          />
        ) : (
          <>
            {contentQuery.data.business_context ? (
              <div className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm text-foreground">
                {contentQuery.data.business_context}
              </div>
            ) : null}

            <p className="text-xs text-muted-foreground">
              Model name:{" "}
              <span className="font-mono text-foreground">{contentQuery.data.dbt_model_name}</span> — graded by
              running <span className="font-mono">dbt build --select {contentQuery.data.dbt_model_name}</span> for
              real against the local dbt project.
            </p>

            <div>
              <p className="mb-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                dbt/models/exercises/{contentQuery.data.dbt_model_name}.sql
              </p>
              <SqlEditor value={sql} onChange={setSql} className="h-72" ariaLabel="dbt exercise model editor" />
            </div>

            {revealedHints.length > 0 ? (
              <div className="space-y-2">
                {revealedHints.map((hint, index) => (
                  <div key={index} className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
                    <span className="font-medium text-muted-foreground">Hint {index + 1}: </span>
                    {hint}
                  </div>
                ))}
              </div>
            ) : null}

            {submitMutation.isPending ? (
              <p className="text-sm text-muted-foreground">
                Running <span className="font-mono">dbt build</span> for real — this can take a few seconds…
              </p>
            ) : null}

            {result ? (
              <div
                role="status"
                className={cn(
                  "rounded-lg border px-4 py-3 text-sm",
                  result.passed ? "border-success/30 bg-success/5" : "border-destructive/30 bg-destructive/5",
                )}
              >
                <div className="flex items-center gap-2">
                  {result.passed ? (
                    <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
                  ) : (
                    <XCircle className="size-4 shrink-0 text-destructive" aria-hidden="true" />
                  )}
                  <p className="font-semibold text-foreground">
                    {result.passed ? "Passed!" : result.model_built ? "Built, but tests failed." : "Build failed."}
                  </p>
                  <span className="ml-auto text-xs text-muted-foreground">Score: {result.score}%</span>
                </div>

                {result.test_outcomes.length > 0 ? (
                  <ul className="mt-3 space-y-1.5">
                    {result.test_outcomes.map((outcome) => (
                      <TestOutcomeRow key={outcome.name} outcome={outcome} />
                    ))}
                  </ul>
                ) : null}

                {!result.model_built && result.log ? (
                  <pre className="mt-3 max-h-64 overflow-auto rounded-md bg-muted/50 p-2 font-mono text-[11px] whitespace-pre-wrap text-muted-foreground">
                    {result.log}
                  </pre>
                ) : null}

                {result.passed && result.explanation ? (
                  <p className="mt-3 text-muted-foreground">{result.explanation}</p>
                ) : null}
              </div>
            ) : null}

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <Button onClick={handleSubmit} disabled={!canSubmit}>
                {submitMutation.isPending ? "Building…" : "Submit"}
              </Button>

              <Button variant="outline" onClick={reset}>
                <RotateCcw className="size-4" aria-hidden="true" />
                Reset
              </Button>

              {exercise.hint_count > 0 && revealedHints.length < exercise.hint_count ? (
                <Button variant="ghost" onClick={handleHint} disabled={hintMutation.isPending}>
                  <Lightbulb className="size-4" aria-hidden="true" />
                  {revealedHints.length === 0 ? "Show hint" : "Show next hint"}
                </Button>
              ) : null}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
