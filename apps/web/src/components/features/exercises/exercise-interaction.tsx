"use client";

import { useState } from "react";
import { CheckCircle2, Lightbulb, RotateCcw, XCircle } from "lucide-react";
import { AUTO_GRADABLE_EXERCISE_TYPES } from "@data-analyst-lab/shared";

import { DifficultyBadge } from "@/components/features/curriculum/difficulty-badge";
import { DbtExerciseWorkspace } from "@/components/features/exercises/dbt-exercise-workspace";
import { PythonExerciseWorkspace } from "@/components/features/exercises/python-exercise-workspace";
import { SqlExerciseWorkspace } from "@/components/features/exercises/sql-exercise-workspace";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useRevealExerciseHint } from "@/features/exercises/use-exercise-hint";
import { useSubmitExerciseAttempt } from "@/features/exercises/use-exercise-attempt";
import { useExerciseContent } from "@/features/exercises/use-exercise-content";
import { useRevealExerciseSolution } from "@/features/exercises/use-exercise-solution";
import { cn } from "@/lib/utils";

const TYPE_LABEL: Record<string, string> = {
  MULTIPLE_CHOICE: "Multiple Choice",
  TRUE_FALSE: "True / False",
  SHORT_ANSWER: "Short Answer",
  CODE: "Code",
  SQL: "SQL",
  PYTHON: "Python",
  DBT: "dbt",
  BUSINESS_REASONING: "Business Reasoning",
  DATA_INTERPRETATION: "Data Interpretation",
  MODELING: "Modeling",
  INTERVIEW_RESPONSE: "Interview Response",
};

interface ExerciseInteractionProps {
  slug: string;
  /** Exposed so a page can wire an "R" keyboard shortcut to it. */
  onRetryRef?: (retry: () => void) => void;
}

export function ExerciseInteraction({ slug, onRetryRef }: ExerciseInteractionProps) {
  const contentQuery = useExerciseContent(slug);
  const submitMutation = useSubmitExerciseAttempt(slug);
  const hintMutation = useRevealExerciseHint(slug);
  const solutionMutation = useRevealExerciseSolution(slug);

  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [freeTextAnswer, setFreeTextAnswer] = useState("");
  const [revealedHints, setRevealedHints] = useState<string[]>([]);

  const reset = () => {
    setSelectedChoice(null);
    setFreeTextAnswer("");
    setRevealedHints([]);
    submitMutation.reset();
    solutionMutation.reset();
  };
  onRetryRef?.(reset);

  if (contentQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-64" />;
  }
  if (contentQuery.isError || !contentQuery.data) {
    return (
      <ErrorState
        title="Unable to load this exercise"
        message="We couldn't reach the API to load this exercise."
        retry={() => void contentQuery.refetch()}
      />
    );
  }

  const exercise = contentQuery.data;

  if (exercise.exercise_type === "SQL") {
    return <SqlExerciseWorkspace slug={slug} exercise={exercise} onRetryRef={onRetryRef} />;
  }

  if (exercise.exercise_type === "PYTHON") {
    return <PythonExerciseWorkspace slug={slug} exercise={exercise} onRetryRef={onRetryRef} />;
  }

  if (exercise.exercise_type === "DBT") {
    return <DbtExerciseWorkspace slug={slug} exercise={exercise} onRetryRef={onRetryRef} />;
  }

  const isChoiceType = exercise.exercise_type === "MULTIPLE_CHOICE" || exercise.exercise_type === "TRUE_FALSE";
  const isAutoGradable = (AUTO_GRADABLE_EXERCISE_TYPES as string[]).includes(exercise.exercise_type);
  const result = submitMutation.data;
  const answered = Boolean(result);
  const submittedAnswer = isChoiceType ? selectedChoice : freeTextAnswer;
  const canSubmit = Boolean(submittedAnswer && submittedAnswer.trim().length > 0) && !answered;

  const choices =
    exercise.choices ?? (exercise.exercise_type === "TRUE_FALSE" ? ["True", "False"] : null);

  function handleSubmit() {
    if (!submittedAnswer) return;
    submitMutation.mutate({ submitted_answer: submittedAnswer });
  }

  function handleHint() {
    hintMutation.mutate(undefined, {
      onSuccess: (response) => setRevealedHints((prev) => [...prev, response.hint]),
    });
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{TYPE_LABEL[exercise.exercise_type] ?? exercise.exercise_type}</Badge>
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
            Attempt {exercise.attempt_count + (answered ? 0 : 1)}
            {exercise.best_attempt?.score != null ? ` · best score so far: ${exercise.best_attempt.score}%` : ""}
          </p>
        ) : null}

        {isChoiceType && choices ? (
          <div role="radiogroup" aria-label={exercise.prompt} className="space-y-2">
            {choices.map((choice) => {
              const isSelected = selectedChoice === choice;
              const isRight = answered && result?.correct_answer === choice;
              const isWrongPick = answered && isSelected && !isRight;
              return (
                <button
                  key={choice}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  disabled={answered}
                  onClick={() => setSelectedChoice(choice)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
                    !answered && "border-border hover:border-primary/50 hover:bg-accent/40",
                    isRight && "border-success bg-success/10",
                    isWrongPick && "border-destructive bg-destructive/10",
                    answered && !isSelected && !isRight && "border-border opacity-60",
                    !answered && isSelected && "border-primary bg-accent/40",
                  )}
                >
                  {isRight ? (
                    <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
                  ) : isWrongPick ? (
                    <XCircle className="size-4 shrink-0 text-destructive" aria-hidden="true" />
                  ) : (
                    <span className="size-4 shrink-0 rounded-full border border-muted-foreground" aria-hidden="true" />
                  )}
                  <span className="text-foreground">{choice}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <Textarea
            value={freeTextAnswer}
            onChange={(event) => setFreeTextAnswer(event.target.value)}
            disabled={answered}
            placeholder="Type your answer..."
            rows={5}
            aria-label="Your answer"
          />
        )}

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

        {result ? (
          <div
            role="status"
            className={cn(
              "rounded-lg border px-4 py-3 text-sm",
              result.is_auto_graded
                ? result.attempt.status === "PASSED"
                  ? "border-success/30 bg-success/5"
                  : "border-destructive/30 bg-destructive/5"
                : "border-border bg-muted/30",
            )}
          >
            <p className="font-semibold text-foreground">
              {result.is_auto_graded
                ? result.attempt.status === "PASSED"
                  ? "Correct!"
                  : "Not quite."
                : "Answer recorded."}
            </p>
            {!result.is_auto_graded ? (
              <p className="mt-1 text-muted-foreground">
                This exercise type doesn&apos;t have an execution engine yet — check the solution below
                and self-assess.
              </p>
            ) : null}
            {result.correct_answer ? (
              <p className="mt-2 text-muted-foreground">
                <span className="font-medium text-foreground">Correct answer: </span>
                {result.correct_answer}
              </p>
            ) : null}
            {result.explanation ? <p className="mt-2 text-muted-foreground">{result.explanation}</p> : null}
          </div>
        ) : null}

        {solutionMutation.data ? (
          <div className="rounded-lg border border-border bg-muted/30 px-4 py-3 text-sm">
            {solutionMutation.data.solution ? (
              <p className="whitespace-pre-line text-foreground">{solutionMutation.data.solution}</p>
            ) : null}
            <p className="mt-2 text-muted-foreground">{solutionMutation.data.explanation}</p>
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-2 pt-1">
          {!answered ? (
            <Button onClick={handleSubmit} disabled={!canSubmit || submitMutation.isPending}>
              {submitMutation.isPending ? "Submitting..." : "Submit"}
            </Button>
          ) : (
            <Button variant="outline" onClick={reset}>
              <RotateCcw className="size-4" aria-hidden="true" />
              Try Again
            </Button>
          )}

          {exercise.hint_count > 0 && revealedHints.length < exercise.hint_count && !answered ? (
            <Button variant="ghost" onClick={handleHint} disabled={hintMutation.isPending}>
              <Lightbulb className="size-4" aria-hidden="true" />
              {revealedHints.length === 0 ? "Show hint" : "Show next hint"}
            </Button>
          ) : null}

          {!isAutoGradable && !solutionMutation.data ? (
            <Button variant="ghost" onClick={() => solutionMutation.mutate()} disabled={solutionMutation.isPending}>
              Reveal solution
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

export function ExerciseInteractionEmptyState() {
  return (
    <EmptyState
      icon={Lightbulb}
      title="No exercise selected"
      description="Choose an exercise from the practice list to get started."
    />
  );
}
