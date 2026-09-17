"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { CheckCircle2, ChevronDown, ChevronUp, RotateCcw, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_SECTION_TYPE_LABELS } from "@/features/interview/constants";
import { useInterviewReview, useRetryInterview } from "@/features/interview/use-interview";
import { AIInterviewDebrief } from "@/components/features/interview/ai-interview-debrief";
import { InterviewScorecard } from "@/components/features/interview/interview-scorecard";

export function InterviewReviewPage({ interviewId }: { interviewId: string }) {
  const reviewQuery = useInterviewReview(interviewId);
  const retryInterview = useRetryInterview(interviewId);
  const router = useRouter();
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  if (reviewQuery.isLoading) return <LoadingState count={3} itemClassName="h-32" />;
  if (reviewQuery.isError || !reviewQuery.data) {
    return <ErrorState message="We couldn't load this interview's review." retry={() => void reviewQuery.refetch()} />;
  }

  const { interview, questions } = reviewQuery.data;

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function handleRetryFull() {
    retryInterview.mutate({ scope: "FULL" }, { onSuccess: (next) => router.push(`/interview/session/${next.id}`) });
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-foreground">{interview.title}</h2>
          <p className="text-sm text-muted-foreground">{interview.mode.replace(/_/g, " ")} · Completed</p>
        </div>
        <Button variant="outline" onClick={handleRetryFull} disabled={retryInterview.isPending}>
          <RotateCcw className="size-4" aria-hidden="true" />
          Retry Full Interview
        </Button>
      </div>

      {interview.score ? <InterviewScorecard score={interview.score} /> : null}

      {interview.score ? <AIInterviewDebrief interviewId={interviewId} /> : null}

      <Card>
        <CardHeader>
          <CardTitle>Question Review</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {questions.map((q) => {
            const isOpen = expanded.has(q.attempt_id);
            return (
              <div key={q.attempt_id} className="rounded-xl border border-border">
                <button
                  type="button"
                  onClick={() => toggle(q.attempt_id)}
                  className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
                >
                  <div className="flex items-center gap-2">
                    {q.passed === true ? (
                      <CheckCircle2 className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                    ) : q.passed === false ? (
                      <XCircle className="size-4 shrink-0 text-rose-600 dark:text-rose-400" aria-hidden="true" />
                    ) : null}
                    <span className="font-medium text-foreground">{q.title}</span>
                    <Badge variant="outline">
                      {INTERVIEW_SECTION_TYPE_LABELS[q.interview_type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ?? q.interview_type}
                    </Badge>
                    {q.over_time ? <Badge variant="secondary">Over time</Badge> : null}
                  </div>
                  <div className="flex items-center gap-2">
                    {q.score != null ? <span className="text-sm font-medium text-foreground">{q.score.toFixed(0)}%</span> : null}
                    {isOpen ? <ChevronUp className="size-4" aria-hidden="true" /> : <ChevronDown className="size-4" aria-hidden="true" />}
                  </div>
                </button>
                {isOpen ? (
                  <div className="flex flex-col gap-3 border-t border-border px-4 py-3 text-sm">
                    {q.prompt ? <p className="text-muted-foreground whitespace-pre-line">{q.prompt}</p> : null}
                    {q.submitted_answer ? (
                      <div>
                        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Your answer</p>
                        <pre className="mt-1 overflow-x-auto rounded-lg bg-muted/40 p-2 font-mono text-xs whitespace-pre-wrap">{q.submitted_answer}</pre>
                      </div>
                    ) : null}
                    {q.correct_answer ? (
                      <div>
                        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Correct answer</p>
                        <p className="mt-1 text-foreground">{q.correct_answer}</p>
                      </div>
                    ) : null}
                    {q.explanation ? (
                      <div>
                        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Explanation</p>
                        <p className="mt-1 text-muted-foreground">{q.explanation}</p>
                      </div>
                    ) : null}
                    {q.test_outcomes.length > 0 ? (
                      <div>
                        <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">Test results</p>
                        <ul className="mt-1 flex flex-col gap-1">
                          {q.test_outcomes.map((outcome, i) => (
                            <li key={i} className="flex items-center gap-1.5">
                              {outcome.passed ? (
                                <CheckCircle2 className="size-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
                              ) : (
                                <XCircle className="size-3.5 shrink-0 text-rose-600 dark:text-rose-400" aria-hidden="true" />
                              )}
                              <span>{outcome.name}</span>
                              {outcome.is_hidden ? <Badge variant="outline" className="text-[10px]">hidden</Badge> : null}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {q.recommended_lesson_slug ? (
                      <Link href={`/learn?lesson=${q.recommended_lesson_slug}`} className="text-sm font-medium text-primary hover:underline">
                        Review: {q.recommended_lesson_title}
                      </Link>
                    ) : null}
                    {q.question_slug ? (
                      <div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            router.push(`/interview/questions/${q.question_slug}`);
                          }}
                        >
                          View question details
                        </Button>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
