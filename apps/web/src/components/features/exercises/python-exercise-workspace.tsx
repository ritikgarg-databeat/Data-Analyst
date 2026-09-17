"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Lightbulb, RotateCcw, XCircle } from "lucide-react";
import type {
  ExerciseContent,
  PythonDatasetFileSchema,
  PythonExecutionResultSchema,
  PythonTestOutcomeSchema,
} from "@data-analyst-lab/shared";

import { DifficultyBadge } from "@/components/features/curriculum/difficulty-badge";
import { PythonCellEditor } from "@/components/features/python-lab/python-cell-editor";
import { PythonOutputPanel } from "@/components/features/python-lab/python-output-panel";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useRevealExerciseHint } from "@/features/exercises/use-exercise-hint";
import { useDestroyPythonRuntime } from "@/features/python/use-python-destroy-runtime";
import { usePythonExecute } from "@/features/python/use-python-execute";
import { usePythonExerciseContent } from "@/features/python/use-python-exercise-content";
import { useCreatePythonRuntime } from "@/features/python/use-python-runtimes";
import { useSubmitPythonExercise } from "@/features/python/use-submit-python-exercise";
import { ApiError } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface PythonExerciseWorkspaceProps {
  slug: string;
  /** Already-loaded generic exercise content (title/description/badges/hints) — fetched once by the caller. */
  exercise: ExerciseContent;
  /** Exposed so a page can wire an "R" keyboard shortcut to it, same contract as `ExerciseInteraction`/`SqlExerciseWorkspace`. */
  onRetryRef?: (retry: () => void) => void;
}

/** Builds the same "load every configured dataset file as a DataFrame" preamble the grading
 * pipeline runs before both the student's and the reference solution's code — see
 * PythonExerciseService._dataset_setup_code on the backend. Run once per runtime so a Run
 * click's own code can reference `orders`, `customers`, etc. straight away. */
function buildSetupCode(files: PythonDatasetFileSchema[]): string {
  const lines = ["import pandas as pd", "import numpy as np"];
  for (const file of files) lines.push(file.suggested_code);
  return lines.join("\n");
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

function TestOutcomeRow({ outcome }: { outcome: PythonTestOutcomeSchema }) {
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
 * Python-specific exercise body, rendered by `ExerciseInteraction` when
 * `exercise.exercise_type === "PYTHON"` instead of the generic choice/free-text UI.
 * "Run" starts (or reuses) a real sandbox runtime, loads the exercise's dataset files, and
 * executes the current code for exploration — never graded. "Submit" sends the code to
 * `POST /python/exercises/{slug}/submit`, which grades it server-side in its own fresh,
 * ephemeral runtimes (see PythonExerciseService.submit) — this workspace's own runtime is
 * never used for grading.
 */
export function PythonExerciseWorkspace({ slug, exercise, onRetryRef }: PythonExerciseWorkspaceProps) {
  const contentQuery = usePythonExerciseContent(slug);
  const createRuntime = useCreatePythonRuntime();
  const destroyRuntime = useDestroyPythonRuntime();
  const executeMutation = usePythonExecute();
  const submitMutation = useSubmitPythonExercise(slug);
  const hintMutation = useRevealExerciseHint(slug);

  const [code, setCode] = useState("");
  const [revealedHints, setRevealedHints] = useState<string[]>([]);
  const [runResult, setRunResult] = useState<PythonExecutionResultSchema | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const initializedCodeRef = useRef(false);

  const [runtimeId, setRuntimeId] = useState<string | null>(null);
  const [setupDone, setSetupDone] = useState(false);

  useEffect(() => {
    if (!initializedCodeRef.current && contentQuery.data) {
      setCode(contentQuery.data.starter_code ?? "");
      initializedCodeRef.current = true;
    }
  }, [contentQuery.data]);

  // Keep a ref mirror of `runtimeId` so the unmount cleanup below always sees the latest value —
  // refs may only be read inside effects/event handlers, never inside `reset` itself (which is
  // handed to the caller via `onRetryRef` and could, as far as the type checker knows, be invoked
  // synchronously during render).
  const runtimeIdRef = useRef<string | null>(null);
  useEffect(() => {
    runtimeIdRef.current = runtimeId;
  }, [runtimeId]);

  // Best-effort teardown of this session's own exploration runtime on unmount.
  useEffect(
    () => () => {
      if (runtimeIdRef.current) destroyRuntime.mutate(runtimeIdRef.current);
    },
    [destroyRuntime],
  );

  function reset() {
    setCode(contentQuery.data?.starter_code ?? "");
    setRevealedHints([]);
    setRunResult(null);
    setRunError(null);
    executeMutation.reset();
    submitMutation.reset();
    if (runtimeId) destroyRuntime.mutate(runtimeId);
    setRuntimeId(null);
    setSetupDone(false);
  }
  onRetryRef?.(reset);

  async function ensureReadyRuntime(): Promise<string> {
    let rtId = runtimeId;
    if (!rtId) {
      const runtime = await createRuntime.mutateAsync(undefined);
      rtId = runtime.id;
      setRuntimeId(rtId);
    }
    if (!setupDone) {
      const setupCode = buildSetupCode(contentQuery.data?.dataset_files ?? []);
      await executeMutation.mutateAsync({ runtimeId: rtId, body: { code: setupCode } });
      setSetupDone(true);
    }
    return rtId;
  }

  const canRun = code.trim().length > 0 && !executeMutation.isPending && Boolean(contentQuery.data?.dataset);
  const canSubmit = code.trim().length > 0 && !submitMutation.isPending;

  async function handleRun() {
    if (!canRun) return;
    setRunError(null);
    try {
      const rtId = await ensureReadyRuntime();
      const result = await executeMutation.mutateAsync({ runtimeId: rtId, body: { code } });
      setRunResult(result);
    } catch (error) {
      setRunError(errorMessage(error));
    }
  }

  function handleSubmit() {
    if (!canSubmit) return;
    submitMutation.mutate({ submitted_code: code });
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
          <Badge variant="outline">Python</Badge>
          <DifficultyBadge difficulty={exercise.difficulty} />
          {exercise.skill_slug ? <Badge variant="secondary">{exercise.skill_slug}</Badge> : null}
          <span className="ml-auto text-xs text-muted-foreground">{exercise.points} pts</span>
        </div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{exercise.title}</h1>
        {exercise.description ? <p className="text-sm text-muted-foreground">{exercise.description}</p> : null}
      </CardHeader>

      <CardContent className="space-y-5">
        <p className="whitespace-pre-line text-sm text-foreground">{exercise.prompt}</p>

        {exercise.attempt_count > 0 ? (
          <p className="text-xs text-muted-foreground">
            Attempt {exercise.attempt_count + (submitResult ? 0 : 1)}
            {exercise.best_attempt?.score != null ? ` · best score so far: ${exercise.best_attempt.score}%` : ""}
          </p>
        ) : null}

        {contentQuery.isLoading ? (
          <LoadingState count={1} itemClassName="h-64" />
        ) : contentQuery.isError || !contentQuery.data ? (
          <ErrorState
            title="Unable to load Python exercise details"
            message="We couldn't reach the API to load this exercise's dataset and starter code."
            retry={() => void contentQuery.refetch()}
          />
        ) : (
          <>
            {contentQuery.data.business_context ? (
              <div className="rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm text-foreground">
                {contentQuery.data.business_context}
              </div>
            ) : null}

            {contentQuery.data.dataset_files.length > 0 ? (
              <div>
                <p className="mb-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                  Dataset files
                </p>
                <div className="overflow-x-auto rounded-lg border border-border">
                  <table className="w-full min-w-max border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-border bg-muted/50 text-left font-medium text-muted-foreground uppercase">
                        <th scope="col" className="px-3 py-2">
                          File
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
                      {contentQuery.data.dataset_files.map((file) => (
                        <tr key={file.container_path} className="border-b border-border last:border-0">
                          <td className="px-3 py-2 font-mono text-foreground">{file.label}</td>
                          <td className="px-3 py-2 text-muted-foreground">{file.grain ?? "—"}</td>
                          <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                            {file.row_count != null ? file.row_count.toLocaleString() : "—"}
                          </td>
                          <td className="px-3 py-2 text-right tabular-nums text-muted-foreground">
                            {file.column_count ?? "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}

            <div>
              <p className="mb-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">Your code</p>
              <PythonCellEditor
                value={code}
                onChange={setCode}
                onRun={() => void handleRun()}
                isRunning={executeMutation.isPending}
                className="h-72"
                ariaLabel="Python exercise code editor"
              />
            </div>

            {runError ? (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive"
              >
                <AlertTriangle className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
                {runError}
              </div>
            ) : null}

            {executeMutation.isPending ? (
              <LoadingState count={1} itemClassName="h-40" />
            ) : runResult ? (
              <div className="space-y-3">
                <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Run output</p>
                <PythonOutputPanel result={runResult} />
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
                  Submitted code output
                </p>
                <PythonOutputPanel result={submitResult.result} />
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
