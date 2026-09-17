"use client";

import Link from "next/link";
import { Briefcase, FileText, GraduationCap, LayoutGrid, Sparkles, Target } from "lucide-react";
import type { NextBestActionSource } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { useNextBestActions } from "@/features/platform/use-platform";

const SOURCE_LABEL: Record<NextBestActionSource, string> = {
  lesson: "Lesson",
  interview: "Interview",
  job_description: "Job Description",
  portfolio: "Portfolio",
  goal: "Goal",
};

const SOURCE_ICON: Record<NextBestActionSource, typeof Target> = {
  lesson: GraduationCap,
  interview: Briefcase,
  job_description: FileText,
  portfolio: LayoutGrid,
  goal: Target,
};

/**
 * "Next Best Action" (Phase 12) — cross-domain counterpart to Today's
 * Mission: Today's Mission only ever recommends a lesson, this pulls from
 * anywhere (interview prep, saved job descriptions, portfolio, goals) via
 * GET /platform/next-best-actions. Visually mirrors TodaysMissionCard.
 */
export function NextBestActionCard() {
  const { data, isLoading, isError, refetch } = useNextBestActions(3);

  if (isLoading) {
    return <LoadingState count={3} itemClassName="h-24" />;
  }
  if (isError) {
    return (
      <ErrorState
        title="Unable to load next best actions"
        message="We couldn't reach the API to load cross-domain recommendations."
        retry={() => void refetch()}
      />
    );
  }

  const actions = data?.actions ?? [];
  if (actions.length === 0) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Nothing queued yet"
        description="As you add target roles, job descriptions, or a portfolio, the platform will suggest what to do next here."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {actions.map((action, index) => {
        const Icon = SOURCE_ICON[action.source];
        return (
          <Link
            key={`${action.source}-${index}`}
            href={action.url_path}
            className="block rounded-xl border border-border bg-card px-4 py-4 transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <div className="mb-2 flex items-center justify-between">
              <Badge variant="outline">
                <Icon className="size-3" aria-hidden="true" />
                {SOURCE_LABEL[action.source]}
              </Badge>
            </div>
            <p className="text-sm font-medium text-foreground">{action.title}</p>
            <p className="mt-1 text-xs text-muted-foreground">{action.why}</p>
          </Link>
        );
      })}
    </div>
  );
}
