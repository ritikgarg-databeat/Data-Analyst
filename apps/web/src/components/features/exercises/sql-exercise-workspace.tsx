"use client";

import { useEffect, useRef, useState } from "react";
import { CheckCircle2, Lightbulb, RotateCcw, XCircle } from "lucide-react";
import type { ExerciseContent, SubmitSqlExerciseResponse } from "@data-analyst-lab/shared";

import { DifficultyBadge } from "@/components/features/curriculum/difficulty-badge";
import { ResultsGrid } from "@/components/features/sql-lab/results-grid";
import { SqlEditor } from "@/components/features/sql-lab/sql-editor";
import { SqlErrorPanel } from "@/components/features/sql-lab/sql-error-panel";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useRevealExerciseHint } from "@/features/exercises/use-exercise-hint";
import { useSqlExecute } from "@/features/sql/use-sql-execute";
import { useSqlExerciseContent } from "@/features/sql/use-sql-exercise-content";
import { useSubmitSqlExercise } from "@/features/sql/use-submit-sql-exercise";
import { cn } from "@/lib/utils";

/** SQL exercises are always executed against DuckDB — the same default the SQL Lab playground uses. */
const EXERCISE_ENGINE = "duckdb";

interface SqlExerciseWorkspaceProps {
  slug: string;
  /** Already-loaded generic exercise content (title/description/badges/hints) — fetched once by the caller. */
  exercise: ExerciseContent;
  /** Exposed so a page can wire an "R" keyboard shortcut to it, same contract as `ExerciseInteraction`. */
  onRetryRef?: (retry: () => void) => void;
}

function TestOutcomeRow({ outcome }: { outcome: SubmitSqlExerciseResponse["test_outcomes"][number] }) {
  return (
    <li className="flex items-start gap-2 text-xs">
      {outcome.passed ? (
        <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-success" aria-hidden="true" />
      ) : (
        <XCircle className="mt-0.5 size-3.5 shrink-0 text-destructive" aria-hidden="true" />
      )}
      <div className="min-w-0">
        <span className="font-medium text-foreground">{outcome.name}</span>
        {outcome.is_hidden ? (
          <Badge variant="outline" className="ml-1.5 px-1 py-0 text-[10px]">
            hidden
          </Badge>
        ) : null}
        {outcome.message ? <p className="mt-0.5 text-muted-foreground">{outcome.message}</p> : null}
      </div>
    </li>
  );
}

/**
 * SQL-specific exercise body, rendered by `ExerciseInteraction` when
 * `exercise.exercise_type === "SQL"` instead of the generic choice/free-text UI.
 * "Run" executes the current query for exploration (no grading); "Submit"
 * grades it against the exercise's (hidden) test suite via the real engine.
 */
export function SqlExerciseWorkspace({ slug, exercise, onRetryRef }: SqlExerciseWorkspaceProps) {
  const sqlContentQuery = useSqlExerciseContent(slug);
  const executeMutation = useSqlExecute();
  const submitMutation = useSubmitSqlExercise(slug);
  const hintMutation = useRevealExerciseHint(slug);

  const [query, setQuery] = useState("");
  const [revealedHints, setRevealedHints] = useState<string[]>([]);
  const initializedQueryRef = useRef(false);

  useEffect(() => {
    if (!initializedQueryRef.current && sqlContentQuery.data) {
      setQuery(sqlContentQuery.data.starter_query ?? "");
      initializedQueryRef.current = true;
    }
  }, [sqlContentQuery.data]);

  function reset() {
    setQuery(sqlContentQuery.data?.starter_query ?? "");
    setRevealedHints([]);
    executeMutation.reset();
    submitMutation.reset();
  }
  onRetryRef?.(reset);

  const dataset = sqlContentQuery.data?.dataset;
  const canRun = query.trim().length > 0 && !executeMutation.isPending && Boolean(dataset);
  const canSubmit = query.trim().length > 0 && !submitMutation.isPending;

  function handleRun() {
    if (!canRun || !dataset) return;
    executeMutation.mutate({ engine: EXERCISE_ENGINE, database: dataset, query });
  }

  function handleSubmit() {
    if (!canSubmit) return;
    submitMutation.mutate({ submitted_query: query });
  }

  function handleHint() {
    hintMutation.mutate(undefined, {
      onSuccess: (response) => setRevealedHints((prev) => [...prev, response.hint]),
    });
  }

  const submitResult = submitMutation.data;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">SQL</Badge>
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

        {exercise.attempt_count > 0 ? (
          <p className="text-xs text-muted-foreground">
            Attempt {exercise.attempt_count + (submitResult ? 0 : 1)}
            {exercise.best_attempt?.score != null ? ` · best score so far: ${exercise.best_attempt.score}%` : ""}
          </p>
        ) : null}

        {sqlContentQuery.isLoading ? (
          <LoadingState count={1} itemClassName="h-64" />
        ) : sqlContentQuery.isError || !sqlContentQuery.data ? (
          <ErrorState
            title="Unable to load SQL exercise details"
            message="We couldn't reach the API to load this exercise's schema and starter query."
            retry={() => void sqlContentQuery.refetch()}
          />
        ) : (
          <>
            {sqlContentQuery.data.business_context ? (
              <div className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm text-foreground">
                {sqlContentQuery.data.business_context}
              </div>
            ) : null}

            {sqlContentQuery.data.tables.length > 0 ? (
              <div>
                <p className="mb-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Tables</p>
                <div className="overflow-x-auto rounded-lg border border-border">
                  <table className="w-full min-w-max border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-border bg-muted/50 text-left font-medium text-muted-foreground uppercase">
                        <th scope="col" className="px-3 py-2">
                          Table
                        </th>
                        <th scope="col" className="px-3 py-2">
                          Grain
                        </th>
                        <th scope="col" className="px-3 py-2 text-right">
                          Rows
                        </th>
                        <th scope="col" className="px-3 py-2 text-right">
                          Columns
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sqlContentQuery.data.tables.map((table) => (
                        <tr key={table.table_name} className="border-b border-border last:border-0">
                          <td className="px-3 py-2 font-mono text-foreground">{table.table_name}</td>
                          <td className="px-3 py-2 text-muted-foreground">{table.grain ?? "—"}</td>
                          <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                            {table.row_count != null ? table.row_count.toLocaleString() : "—"}
                          </td>
                          <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                            {table.column_count ?? "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}

            <div>
              <p className="mb-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                Your query
              </p>
              <SqlEditor
                value={query}
                onChange={setQuery}
                onRun={handleRun}
                isRunning={executeMutation.isPending}
                className="h-72"
                ariaLabel="SQL exercise query editor"
              />
            </div>

            {executeMutation.isPending ? (
              <LoadingState count={1} itemClassName="h-40" />
            ) : executeMutation.data ? (
              <div className="space-y-3">
                <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Run output</p>
                <SqlErrorPanel error={executeMutation.data.error} />
                {executeMutation.data.status === "success" ? (
                  <ResultsGrid
                    columns={executeMutation.data.columns}
                    rows={executeMutation.data.rows}
                    rowCount={executeMutation.data.row_count}
                    truncated={executeMutation.data.truncated}
                  />
                ) : null}
              </div>
            ) : null}

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

            {submitResult ? (
              <div
                role="status"
                className={cn(
                  "rounded-lg border px-4 py-3 text-sm",
                  submitResult.passed ? "border-success/30 bg-success/5" : "border-destructive/30 bg-destructive/5",
                )}
              >
                <div className="flex items-center gap-2">
                  {submitResult.passed ? (
                    <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
                  ) : (
                    <XCircle className="size-4 shrink-0 text-destructive" aria-hidden="true" />
                  )}
                  <p className="font-semibold text-foreground">{submitResult.passed ? "Passed!" : "Not quite."}</p>
                  {submitResult.score != null ? (
                    <span className="ml-auto text-xs text-muted-foreground">Score: {submitResult.score}%</span>
                  ) : null}
                </div>

                {submitResult.test_outcomes.length > 0 ? (
                  <ul className="mt-3 space-y-1.5">
                    {submitResult.test_outcomes.map((outcome) => (
                      <TestOutcomeRow key={outcome.name} outcome={outcome} />
                    ))}
                  </ul>
                ) : null}

                {submitResult.passed && submitResult.explanation ? (
                  <p className="mt-3 text-muted-foreground">{submitResult.explanation}</p>
                ) : null}
              </div>
            ) : null}

            {submitResult ? (
              <div className="space-y-3">
                <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                  Submitted query output
                </p>
                <SqlErrorPanel error={submitResult.result.error} />
                {submitResult.result.status === "success" ? (
                  <ResultsGrid
                    columns={submitResult.result.columns}
                    rows={submitResult.result.rows}
                    rowCount={submitResult.result.row_count}
                    truncated={submitResult.result.truncated}
                  />
                ) : null}
              </div>
            ) : null}

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <Button onClick={handleSubmit} disabled={!canSubmit}>
                {submitMutation.isPending ? "Submitting..." : "Submit"}
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
