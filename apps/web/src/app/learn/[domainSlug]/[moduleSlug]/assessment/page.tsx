"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { CheckCircle2, ClipboardCheck, XCircle } from "lucide-react";

import { LessonBreadcrumb } from "@/components/features/lesson-reader/lesson-breadcrumb";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useDomain } from "@/features/domains/use-domain";
import { useModule } from "@/features/modules/use-module";
import { useModuleAssessment } from "@/features/modules/use-module-assessment";
import { useStartAssessment } from "@/features/assessments/use-start-assessment";
import { useSubmitAssessment } from "@/features/assessments/use-submit-assessment";
import type { ExerciseContent, SubmitAssessmentResponse } from "@data-analyst-lab/shared";
import { cn } from "@/lib/utils";

type Stage =
  | { name: "intro" }
  | { name: "in-progress"; attemptId: string; questions: ExerciseContent[]; startedAt: number }
  | { name: "results"; result: SubmitAssessmentResponse; questions: ExerciseContent[] };

export default function AssessmentPage() {
  const params = useParams<{ domainSlug: string; moduleSlug: string }>();
  const { domainSlug, moduleSlug } = params;

  const domainQuery = useDomain(domainSlug);
  const moduleQuery = useModule(moduleSlug);
  const assessmentQuery = useModuleAssessment(moduleSlug, true);
  const assessmentSlug = assessmentQuery.data?.slug ?? "";

  const startMutation = useStartAssessment(assessmentSlug);
  const [stage, setStage] = useState<Stage>({ name: "intro" });
  const [answers, setAnswers] = useState<Record<string, string>>({});

  const submitMutation = useSubmitAssessment(
    assessmentSlug,
    stage.name === "in-progress" ? stage.attemptId : "",
  );

  if (assessmentQuery.isLoading || moduleQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-64" />;
  }
  if (assessmentQuery.isError || !assessmentQuery.data) {
    return (
      <ErrorState
        title="Unable to load this assessment"
        message="This module may not have an assessment, or the API is unreachable."
        retry={() => void assessmentQuery.refetch()}
      />
    );
  }

  const assessment = assessmentQuery.data;

  function handleStart() {
    startMutation.mutate(undefined, {
      onSuccess: (response) => {
        setAnswers({});
        setStage({
          name: "in-progress",
          attemptId: response.attempt.id,
          questions: response.questions,
          startedAt: Date.now(),
        });
      },
    });
  }

  function handleSubmit() {
    if (stage.name !== "in-progress") return;
    const payloadAnswers = stage.questions.map((q) => ({
      exercise_id: q.id,
      submitted_answer: answers[q.id] ?? "",
    }));
    const timeSpent = Math.round((Date.now() - stage.startedAt) / 1000);
    submitMutation.mutate(
      { answers: payloadAnswers, time_spent_seconds: timeSpent },
      { onSuccess: (result) => setStage({ name: "results", result, questions: stage.questions }) },
    );
  }

  return (
    <div className="mx-auto max-w-2xl pb-16">
      <LessonBreadcrumb
        domainSlug={domainSlug}
        domainName={domainQuery.data?.name ?? domainSlug}
        moduleSlug={moduleSlug}
        moduleTitle={moduleQuery.data?.title ?? moduleSlug}
        lessonTitle="Assessment"
      />

      {stage.name === "intro" ? (
        <Card>
          <CardHeader className="items-center text-center">
            <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
              <ClipboardCheck className="size-6" aria-hidden="true" />
            </div>
            <CardTitle className="text-xl">{assessment.title}</CardTitle>
            {assessment.description ? (
              <p className="text-sm text-muted-foreground">{assessment.description}</p>
            ) : null}
          </CardHeader>
          <CardContent className="space-y-4 text-center">
            <div className="flex flex-wrap items-center justify-center gap-2 text-sm text-muted-foreground">
              <Badge variant="outline">{assessment.question_count} Questions</Badge>
              {assessment.time_limit_minutes ? (
                <Badge variant="outline">{assessment.time_limit_minutes} Minutes</Badge>
              ) : null}
              <Badge variant="outline">{assessment.passing_score}% to pass</Badge>
              {assessment.retry_policy === "LIMITED" && assessment.max_attempts ? (
                <Badge variant="outline">Max {assessment.max_attempts} attempts</Badge>
              ) : (
                <Badge variant="outline">Unlimited retries</Badge>
              )}
            </div>
            <Button onClick={handleStart} disabled={startMutation.isPending}>
              {startMutation.isPending ? "Starting..." : "Start Assessment"}
            </Button>
            {startMutation.isError ? (
              <p className="text-sm text-destructive">
                {startMutation.error instanceof Error ? startMutation.error.message : "Couldn't start the assessment."}
              </p>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      {stage.name === "in-progress" ? (
        <div className="space-y-6">
          {stage.questions.map((question, index) => {
            const isChoice = question.exercise_type === "MULTIPLE_CHOICE" || question.exercise_type === "TRUE_FALSE";
            const choices = question.choices ?? (question.exercise_type === "TRUE_FALSE" ? ["True", "False"] : null);
            return (
              <Card key={question.id}>
                <CardHeader>
                  <CardTitle className="text-sm text-muted-foreground">Question {index + 1}</CardTitle>
                  <p className="text-sm font-medium text-foreground">{question.prompt}</p>
                </CardHeader>
                <CardContent>
                  {isChoice && choices ? (
                    <div role="radiogroup" aria-label={question.prompt} className="space-y-2">
                      {choices.map((choice) => (
                        <button
                          key={choice}
                          type="button"
                          role="radio"
                          aria-checked={answers[question.id] === choice}
                          onClick={() => setAnswers((prev) => ({ ...prev, [question.id]: choice }))}
                          className={cn(
                            "block w-full rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                            answers[question.id] === choice
                              ? "border-primary bg-accent/40"
                              : "border-border hover:border-primary/50 hover:bg-accent/40",
                          )}
                        >
                          {choice}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <Textarea
                      value={answers[question.id] ?? ""}
                      onChange={(event) => setAnswers((prev) => ({ ...prev, [question.id]: event.target.value }))}
                      placeholder="Type your answer..."
                      aria-label={`Answer for question ${index + 1}`}
                    />
                  )}
                </CardContent>
              </Card>
            );
          })}

          <Button onClick={handleSubmit} disabled={submitMutation.isPending} size="lg">
            {submitMutation.isPending ? "Submitting..." : "Submit Assessment"}
          </Button>
        </div>
      ) : null}

      {stage.name === "results" ? (
        <div className="space-y-6">
          <Card className={stage.result.passed ? "border-success/40" : "border-destructive/40"}>
            <CardHeader className="items-center text-center">
              {stage.result.passed ? (
                <CheckCircle2 className="size-10 text-success" aria-hidden="true" />
              ) : (
                <XCircle className="size-10 text-destructive" aria-hidden="true" />
              )}
              <CardTitle className="text-xl">{stage.result.passed ? "Passed!" : "Not passed"}</CardTitle>
              <p className="text-sm text-muted-foreground">Score: {stage.result.attempt.score}%</p>
            </CardHeader>
          </Card>

          <div className="space-y-3">
            {stage.result.answers.map((answer, index) => {
              const question = stage.questions.find((q) => q.id === answer.exercise_id);
              return (
                <Card key={answer.exercise_id}>
                  <CardHeader className="flex-row items-center gap-2">
                    {answer.is_correct === true ? (
                      <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
                    ) : answer.is_correct === false ? (
                      <XCircle className="size-4 shrink-0 text-destructive" aria-hidden="true" />
                    ) : null}
                    <CardTitle className="text-sm">Question {index + 1}: {question?.title ?? ""}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-1 text-sm text-muted-foreground">
                    {answer.correct_answer ? (
                      <p>
                        <span className="font-medium text-foreground">Correct answer: </span>
                        {answer.correct_answer}
                      </p>
                    ) : null}
                    <p>{answer.explanation}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Button asChild variant="outline">
            <Link href={`/learn/${domainSlug}/${moduleSlug}`}>Back to Module</Link>
          </Button>
        </div>
      ) : null}
    </div>
  );
}
