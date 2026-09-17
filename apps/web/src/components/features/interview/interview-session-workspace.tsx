"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AlertTriangle, ArrowRight, Pause, Play, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_SECTION_TYPE_LABELS } from "@/features/interview/constants";
import {
  useAbandonInterview,
  useAnswerInterviewQuestion,
  useInterview,
  usePauseInterview,
  useResumeInterview,
  useStartInterview,
} from "@/features/interview/use-interview";
import { InterviewQuestionAnswer } from "@/components/features/interview/interview-question-answer";
import { InterviewTimer } from "@/components/features/interview/interview-timer";

interface InterviewSessionWorkspaceProps {
  interviewId: string;
}

export function InterviewSessionWorkspace({ interviewId }: InterviewSessionWorkspaceProps) {
  const router = useRouter();
  // Refetch periodically while running — this is what lets the frontend
  // notice a Case Study round finishing in the separate Case Workspace, and
  // what re-syncs the display timer against the server's own clock (spec
  // sections 33/34: the server, never the client, is the source of truth).
  const interviewQuery = useInterview(interviewId, { refetchInterval: 15000 });
  const startInterview = useStartInterview();
  const pauseInterview = usePauseInterview();
  const resumeInterview = useResumeInterview();
  const abandonInterview = useAbandonInterview();
  const answerQuestion = useAnswerInterviewQuestion(interviewId);

  const interview = interviewQuery.data;

  useEffect(() => {
    if (interview?.status === "COMPLETED") {
      router.push(`/interview/session/${interviewId}/review`);
    }
  }, [interview?.status, interviewId, router]);

  if (interviewQuery.isLoading) return <LoadingState count={2} itemClassName="h-40" />;
  if (interviewQuery.isError || !interview) {
    return <ErrorState message="We couldn't load this interview." retry={() => void interviewQuery.refetch()} />;
  }

  const currentSection = interview.sections[interview.current_section_index];
  const current = interview.current_question;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{interview.mode.replace(/_/g, " ")}</Badge>
          <Badge variant="secondary">{interview.status.replace(/_/g, " ")}</Badge>
          {currentSection ? (
            <span className="text-sm text-muted-foreground">
              Round {interview.current_section_index + 1} of {interview.sections.length}:{" "}
              {INTERVIEW_SECTION_TYPE_LABELS[currentSection.interview_type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ??
                currentSection.interview_type}
            </span>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <InterviewTimer
            totalTimeLimitSeconds={interview.total_time_limit_seconds}
            timeSpentSeconds={interview.time_spent_seconds}
            startedAt={interview.status === "IN_PROGRESS" ? interview.started_at : null}
            isRunning={interview.status === "IN_PROGRESS"}
            onTimeUp={() => void interviewQuery.refetch()}
          />
          {interview.status === "IN_PROGRESS" ? (
            <Button variant="outline" size="sm" onClick={() => pauseInterview.mutate(interviewId)} disabled={pauseInterview.isPending}>
              <Pause className="size-4" aria-hidden="true" />
              Pause
            </Button>
          ) : null}
          {interview.status !== "COMPLETED" && interview.status !== "ABANDONED" ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => abandonInterview.mutate(interviewId)}
              disabled={abandonInterview.isPending}
            >
              <X className="size-4" aria-hidden="true" />
              Abandon
            </Button>
          ) : null}
        </div>
      </div>

      {interview.status === "NOT_STARTED" ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <p className="text-lg font-medium text-foreground">{interview.title}</p>
            <p className="max-w-md text-sm text-muted-foreground">
              {interview.total_time_limit_seconds
                ? `This interview is timed — ${Math.round(interview.total_time_limit_seconds / 60)} minutes total. The timer starts the moment you begin.`
                : "This is an untimed practice session — work through it at your own pace."}
            </p>
            <Button onClick={() => startInterview.mutate(interviewId)} disabled={startInterview.isPending}>
              <Play className="size-4" aria-hidden="true" />
              {startInterview.isPending ? "Starting..." : "Start Interview"}
            </Button>
          </CardContent>
        </Card>
      ) : interview.status === "PAUSED" ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <Pause className="size-8 text-muted-foreground" aria-hidden="true" />
            <p className="text-lg font-medium text-foreground">Interview paused</p>
            <p className="text-sm text-muted-foreground">Your elapsed time is saved — resume whenever you&apos;re ready.</p>
            <Button onClick={() => resumeInterview.mutate(interviewId)} disabled={resumeInterview.isPending}>
              <Play className="size-4" aria-hidden="true" />
              Resume
            </Button>
          </CardContent>
        </Card>
      ) : interview.status === "ABANDONED" ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 py-10 text-center">
            <AlertTriangle className="size-8 text-muted-foreground" aria-hidden="true" />
            <p className="text-lg font-medium text-foreground">This interview was abandoned</p>
            <Button variant="outline" asChild>
              <Link href="/interview">Back to Interview Prep</Link>
            </Button>
          </CardContent>
        </Card>
      ) : current?.case_attempt_id ? (
        <Card>
          <CardHeader>
            <CardTitle>Case Study Round</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-3 py-6 text-center">
            <p className="text-sm text-muted-foreground">
              This round is a full business case, completed in the Case Workspace. Come back to this page afterward —
              it will automatically pick up where the case left off.
            </p>
            <Button asChild>
              <Link href={`/case-studies/attempts/${current.case_attempt_id}`}>
                Continue in Case Workspace
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
            <Button variant="ghost" size="sm" onClick={() => void interviewQuery.refetch()}>
              I&apos;ve finished the case — check status
            </Button>
          </CardContent>
        </Card>
      ) : current?.question ? (
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle>{current.question.title}</CardTitle>
                {current.question.time_limit_seconds ? (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Suggested time: {Math.round(current.question.time_limit_seconds / 60)} min
                  </p>
                ) : null}
              </div>
              <Badge variant="outline">
                {INTERVIEW_SECTION_TYPE_LABELS[current.question.interview_type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ??
                  current.question.interview_type}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {current.question.business_context ? (
              <p className="rounded-lg bg-muted/30 p-3 text-sm text-muted-foreground">{current.question.business_context}</p>
            ) : null}
            <p className="text-sm text-foreground whitespace-pre-line">{current.question.prompt}</p>
            {answerQuestion.data && !answerQuestion.isPending ? (
              <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                <p className="font-medium text-foreground">
                  {answerQuestion.data.is_auto_graded && answerQuestion.data.score != null
                    ? `Scored ${answerQuestion.data.score.toFixed(0)}%`
                    : "Recorded — moving to the next question."}
                </p>
                {answerQuestion.data.explanation ? (
                  <p className="mt-1 text-muted-foreground">{answerQuestion.data.explanation}</p>
                ) : null}
              </div>
            ) : null}
            <InterviewQuestionAnswer
              key={current.id}
              question={current.question}
              isSubmitting={answerQuestion.isPending}
              onSubmit={(payload) => answerQuestion.mutate(payload)}
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Preparing your next question...
          </CardContent>
        </Card>
      )}
    </div>
  );
}
