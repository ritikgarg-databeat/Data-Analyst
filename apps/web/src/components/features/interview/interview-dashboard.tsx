"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Bookmark,
  Clock,
  History,
  MessagesSquare,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_MODE_DESCRIPTIONS, INTERVIEW_SECTION_TYPE_LABELS } from "@/features/interview/constants";
import { useCreateInterview, useInterviews, useReadiness } from "@/features/interview/use-interview";

const TARGET_PROFILE = "Data Analyst — ~2 Years Experience";

const QUICK_START_MODES = [
  { mode: "PRACTICE" as const, interviewType: "SQL" as const, label: "Practice SQL", icon: Sparkles },
  { mode: "WEAKNESS_DRILL" as const, label: "Drill My Weakest Skill", icon: Target },
  { mode: "MOCK" as const, templateSlug: "mock-interview-standard", label: "Full Mock Interview", icon: MessagesSquare },
  { mode: "FINAL_READINESS" as const, templateSlug: "final-readiness-assessment", label: "Final Readiness Assessment", icon: Clock },
];

function readinessTone(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-rose-600 dark:text-rose-400";
}

export function InterviewDashboard() {
  const readinessQuery = useReadiness();
  const interviewsQuery = useInterviews();
  const createInterview = useCreateInterview();
  const router = useRouter();

  const recent = useMemo(
    () =>
      [...(interviewsQuery.data ?? [])]
        .filter((i) => i.status === "COMPLETED")
        .sort((a, b) => (b.completed_at ?? "").localeCompare(a.completed_at ?? ""))
        .slice(0, 5),
    [interviewsQuery.data],
  );

  const inProgress = useMemo(
    () => (interviewsQuery.data ?? []).find((i) => i.status === "IN_PROGRESS" || i.status === "PAUSED"),
    [interviewsQuery.data],
  );

  const isLoading = readinessQuery.isLoading || interviewsQuery.isLoading;
  const isError = readinessQuery.isError || interviewsQuery.isError;

  function handleQuickStart(quickStart: (typeof QUICK_START_MODES)[number]) {
    createInterview.mutate(
      {
        mode: quickStart.mode,
        template_slug: "templateSlug" in quickStart ? quickStart.templateSlug : undefined,
        interview_type: "interviewType" in quickStart ? quickStart.interviewType : undefined,
        question_count: 5,
        time_limit_seconds: quickStart.mode === "PRACTICE" ? undefined : 1800,
      },
      { onSuccess: (interview) => router.push(`/interview/session/${interview.id}`) },
    );
  }

  if (isLoading) return <LoadingState count={4} itemClassName="h-28" />;
  if (isError) {
    return (
      <ErrorState
        message="We couldn't reach the API to load your interview readiness."
        retry={() => {
          void readinessQuery.refetch();
          void interviewsQuery.refetch();
        }}
      />
    );
  }

  const readiness = readinessQuery.data;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">{TARGET_PROFILE}</Badge>
        {inProgress ? (
          <Button size="sm" variant="outline" asChild>
            <Link href={`/interview/session/${inProgress.id}`}>
              <Clock className="size-4" aria-hidden="true" />
              Resume in-progress interview
            </Link>
          </Button>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Overall Readiness</CardTitle>
          </CardHeader>
          <CardContent>
            {readiness ? (
              <>
                <p className={`text-3xl font-semibold ${readinessTone(readiness.overall_score)}`}>
                  {readiness.overall_score.toFixed(0)}%
                </p>
                <Progress value={readiness.overall_score} className="mt-2" />
                <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                  <div>
                    <p className="font-medium text-foreground">{readiness.mastery_component.toFixed(0)}%</p>
                    Skill mastery
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{readiness.recent_performance_component.toFixed(0)}%</p>
                    Recent performance
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{readiness.consistency_component.toFixed(0)}%</p>
                    Consistency
                  </div>
                </div>
              </>
            ) : (
              "—"
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <TrendingUp className="size-4 text-emerald-600 dark:text-emerald-400" aria-hidden="true" />
              Strongest Areas
            </CardTitle>
          </CardHeader>
          <CardContent>
            {readiness && readiness.strongest.length > 0 ? (
              <ul className="flex flex-col gap-1 text-sm">
                {readiness.strongest.map((type) => (
                  <li key={type} className="text-foreground">
                    {INTERVIEW_SECTION_TYPE_LABELS[type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ?? type}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">Complete a round to see this.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <TrendingDown className="size-4 text-rose-600 dark:text-rose-400" aria-hidden="true" />
              Weakest Areas
            </CardTitle>
          </CardHeader>
          <CardContent>
            {readiness && readiness.weakest.length > 0 ? (
              <ul className="flex flex-col gap-1 text-sm">
                {readiness.weakest.map((type) => (
                  <li key={type} className="text-foreground">
                    {INTERVIEW_SECTION_TYPE_LABELS[type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ?? type}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">Complete a round to see this.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quick Start</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {QUICK_START_MODES.map((quickStart) => {
              const Icon = quickStart.icon;
              return (
                <button
                  key={quickStart.label}
                  type="button"
                  onClick={() => handleQuickStart(quickStart)}
                  disabled={createInterview.isPending}
                  className="flex flex-col items-start gap-2 rounded-xl border border-border bg-card p-4 text-left transition-colors hover:bg-accent disabled:opacity-60"
                >
                  <Icon className="size-5 text-primary" aria-hidden="true" />
                  <span className="font-medium text-foreground">{quickStart.label}</span>
                  <span className="text-xs text-muted-foreground">{INTERVIEW_MODE_DESCRIPTIONS[quickStart.mode]}</span>
                </button>
              );
            })}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href="/interview/questions">Browse question bank</Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/interview/templates">Company-style assessments</Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/interview/plan">
                <Sparkles className="size-4" aria-hidden="true" />
                My 7-Day Plan
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/interview/readiness">
                <History className="size-4" aria-hidden="true" />
                Readiness Trend
              </Link>
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link href="/interview/review">
                <Bookmark className="size-4" aria-hidden="true" />
                My Interview Review
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Scores</CardTitle>
        </CardHeader>
        <CardContent>
          {recent.length === 0 ? (
            <EmptyState
              icon={MessagesSquare}
              title="No completed interviews yet"
              description="Start a practice round above to see your scores here."
            />
          ) : (
            <ul className="flex flex-col gap-2">
              {recent.map((interview) => (
                <li key={interview.id} className="flex items-center justify-between gap-2 text-sm">
                  <Link href={`/interview/session/${interview.id}/review`} className="font-medium text-foreground hover:underline">
                    {interview.title}
                  </Link>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{interview.mode.replace(/_/g, " ")}</Badge>
                    <span className={`font-medium ${readinessTone(interview.score?.overall ?? 0)}`}>
                      {interview.score ? `${interview.score.overall.toFixed(0)}%` : "—"}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
