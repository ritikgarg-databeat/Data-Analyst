"use client";

import { useMemo } from "react";
import Link from "next/link";
import type { CaseAttempt, CaseCategory, CaseListItem } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { CASE_CATEGORY_LABELS } from "@/features/case-studies/constants";
import { useCaseAttempts, useCases } from "@/features/case-studies/use-case-studies";
import { formatDuration } from "@/features/case-studies/utils";
import { BarChart3 } from "lucide-react";

interface CategoryStat {
  category: CaseCategory;
  average: number;
  count: number;
}

interface RubricCategoryStat {
  category: string;
  average: number;
  count: number;
}

/**
 * My Case Performance (spec section 51) — deterministic personal analytics,
 * no AI. Every figure here is computed client-side from two already-existing
 * endpoints (`GET /cases/attempts` for full attempt history, `GET /cases` for
 * each case's category), the same join the workspace uses to resolve a case
 * by id — no new backend endpoint needed.
 */
export function CasePerformanceDashboard() {
  const attemptsQuery = useCaseAttempts();
  const casesQuery = useCases();

  const isLoading = attemptsQuery.isLoading || casesQuery.isLoading;
  const isError = attemptsQuery.isError || casesQuery.isError;

  const stats = useMemo(() => {
    const attempts = attemptsQuery.data ?? [];
    const cases = casesQuery.data ?? [];
    const caseById = new Map(cases.map((item) => [item.case.id, item.case]));

    const completed = attempts.filter((a) => a.status === "COMPLETED" && a.score);
    const distinctCompletedCases = new Set(completed.map((a) => a.case_id));

    const averageScore =
      completed.length > 0 ? completed.reduce((sum, a) => sum + (a.score?.overall ?? 0), 0) / completed.length : null;

    const byCategory = new Map<CaseCategory, { total: number; count: number }>();
    for (const attempt of completed) {
      const category = caseById.get(attempt.case_id)?.category;
      if (!category) continue;
      const entry = byCategory.get(category) ?? { total: 0, count: 0 };
      entry.total += attempt.score?.overall ?? 0;
      entry.count += 1;
      byCategory.set(category, entry);
    }
    const categoryStats: CategoryStat[] = Array.from(byCategory.entries())
      .map(([category, { total, count }]) => ({ category, average: total / count, count }))
      .sort((a, b) => b.average - a.average);
    const strongestDomain = categoryStats[0];
    const weakestDomain = categoryStats[categoryStats.length - 1];

    const totalSeconds = completed.reduce(
      (sum, a) => sum + Object.values(a.time_per_stage_seconds ?? {}).reduce((s, v) => s + v, 0),
      0,
    );
    const averageSeconds = completed.length > 0 ? totalSeconds / completed.length : 0;

    const byRubricCategory = new Map<string, { total: number; count: number }>();
    for (const attempt of completed) {
      for (const cat of attempt.score?.categories ?? []) {
        const entry = byRubricCategory.get(cat.category) ?? { total: 0, count: 0 };
        entry.total += cat.pct;
        entry.count += 1;
        byRubricCategory.set(cat.category, entry);
      }
    }
    const recurringWeaknesses: RubricCategoryStat[] = Array.from(byRubricCategory.entries())
      .map(([category, { total, count }]) => ({ category, average: total / count, count }))
      .filter((r) => r.count >= 2 && r.average < 70)
      .sort((a, b) => a.average - b.average);

    const recent = [...attempts]
      .sort((a, b) => (b.last_activity_at ?? "").localeCompare(a.last_activity_at ?? ""))
      .slice(0, 5)
      .map((attempt) => ({ attempt, case: caseById.get(attempt.case_id) }));

    const notStartedInWeakestDomain = weakestDomain
      ? cases.find((item) => item.case.category === weakestDomain.category && item.attempt_status == null)
      : undefined;

    return {
      distinctCompletedCount: distinctCompletedCases.size,
      totalCompletions: completed.length,
      averageScore,
      strongestDomain,
      weakestDomain,
      averageSeconds,
      recurringWeaknesses,
      recent,
      recommendedNext: notStartedInWeakestDomain,
    };
  }, [attemptsQuery.data, casesQuery.data]);

  if (isLoading) return <LoadingState count={4} itemClassName="h-28" />;
  if (isError) {
    return (
      <ErrorState
        message="We couldn't reach the API to load your case performance."
        retry={() => {
          void attemptsQuery.refetch();
          void casesQuery.refetch();
        }}
      />
    );
  }

  if (stats.totalCompletions === 0) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No completed cases yet"
        description="Complete a case study to start seeing your performance here — strongest/weakest domains, average time, and recurring weak areas."
        action={{ label: "Browse Case Studies", href: "/case-studies" }}
      />
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Cases Completed</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-foreground">
            {stats.distinctCompletedCount}
            <span className="ml-1 text-sm font-normal text-muted-foreground">
              ({stats.totalCompletions} attempt{stats.totalCompletions === 1 ? "" : "s"})
            </span>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Average Score</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold text-foreground">
            {stats.averageScore != null ? `${stats.averageScore.toFixed(0)}%` : "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Strongest Domain</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.strongestDomain ? (
              <>
                <p className="font-medium text-foreground">{CASE_CATEGORY_LABELS[stats.strongestDomain.category]}</p>
                <p className="text-sm text-muted-foreground">{stats.strongestDomain.average.toFixed(0)}% avg</p>
              </>
            ) : (
              "—"
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Weakest Domain</CardTitle>
          </CardHeader>
          <CardContent>
            {stats.weakestDomain ? (
              <>
                <p className="font-medium text-foreground">{CASE_CATEGORY_LABELS[stats.weakestDomain.category]}</p>
                <p className="text-sm text-muted-foreground">{stats.weakestDomain.average.toFixed(0)}% avg</p>
              </>
            ) : (
              "—"
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Average Time per Completed Case</CardTitle>
        </CardHeader>
        <CardContent className="text-foreground">{formatDuration(stats.averageSeconds)}</CardContent>
      </Card>

      {stats.recurringWeaknesses.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Recurring Weak Areas</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-1.5 text-sm">
              {stats.recurringWeaknesses.map((weakness) => (
                <li key={weakness.category} className="flex items-center justify-between">
                  <span className="text-foreground">{weakness.category}</span>
                  <span className="text-muted-foreground">
                    {weakness.average.toFixed(0)}% avg across {weakness.count} attempts
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      {stats.recommendedNext ? (
        <Card>
          <CardHeader>
            <CardTitle>Recommended Next Case</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center justify-between">
            <div>
              <p className="font-medium text-foreground">{stats.recommendedNext.case.title}</p>
              <p className="text-sm text-muted-foreground">
                In your weakest domain — {CASE_CATEGORY_LABELS[stats.recommendedNext.case.category]}
              </p>
            </div>
            <Link href={`/case-studies/${stats.recommendedNext.case.slug}`} className="text-sm font-medium text-primary hover:underline">
              View case →
            </Link>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Recent Cases</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-2">
            {stats.recent.map(({ attempt, case: c }: { attempt: CaseAttempt; case: CaseListItem["case"] | undefined }) => (
              <li key={attempt.id} className="flex items-center justify-between gap-2 text-sm">
                <Link
                  href={`/case-studies/attempts/${attempt.id}`}
                  className="font-medium text-foreground hover:underline"
                >
                  {c?.title ?? "Unknown case"}
                </Link>
                <Badge variant="outline">{attempt.status.replace(/_/g, " ")}</Badge>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
