"use client";

import Link from "next/link";
import { CheckCircle2, Lightbulb, ListChecks, RotateCcw, Target } from "lucide-react";
import type { RecommendationItem } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { useRecommendations } from "@/features/recommendations/use-recommendations";

const REASON_LABEL: Record<RecommendationItem["reason"], string> = {
  incomplete_prerequisite: "Prerequisite",
  next_in_module: "Next Up",
  weak_skill: "Needs Practice",
  unfinished_lesson: "Unfinished",
  review: "Review",
};

const REASON_ICON: Record<RecommendationItem["reason"], typeof Target> = {
  incomplete_prerequisite: ListChecks,
  next_in_module: Target,
  weak_skill: Lightbulb,
  unfinished_lesson: RotateCcw,
  review: CheckCircle2,
};

export function TodaysMissionCard() {
  const { data, isLoading, isError, refetch } = useRecommendations(3);

  if (isLoading) {
    return <LoadingState count={3} itemClassName="h-24" />;
  }
  if (isError) {
    return (
      <ErrorState
        title="Unable to load today's mission"
        message="We couldn't reach the API to load recommendations."
        retry={() => void refetch()}
      />
    );
  }
  if (!data || data.length === 0) {
    return (
      <EmptyState
        icon={Target}
        title="No mission yet"
        description="Start a lesson and recommendations will appear here based on your progress."
        action={{ label: "Browse the curriculum", href: "/learn" }}
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {data.map((item) => {
        const Icon = REASON_ICON[item.reason];
        return (
          <Link
            key={item.lesson.id}
            href={`/learn/${item.lesson.domain_slug}/${item.lesson.module_slug}/${item.lesson.slug}`}
            className="block rounded-xl border border-border bg-card px-4 py-4 transition-shadow hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <div className="mb-2 flex items-center justify-between">
              <Badge variant="outline">
                <Icon className="size-3" aria-hidden="true" />
                {REASON_LABEL[item.reason]}
              </Badge>
            </div>
            <p className="text-sm font-medium text-foreground">{item.lesson.title}</p>
            <p className="mt-1 text-xs text-muted-foreground">{item.explanation}</p>
          </Link>
        );
      })}
    </div>
  );
}
