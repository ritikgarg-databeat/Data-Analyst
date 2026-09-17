"use client";

import Link from "next/link";
import { RotateCcw } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useRecommendations } from "@/features/recommendations/use-recommendations";

export default function ReviewPage() {
  const { data, isLoading, isError, refetch } = useRecommendations(10);
  const reviewItems = (data ?? []).filter((item) => item.reason === "review");

  return (
    <div>
      <PageHeader
        title="Review"
        subtitle="Lessons whose skill mastery has dipped and could use a revisit."
      />

      {isLoading ? (
        <LoadingState count={3} itemClassName="h-24" />
      ) : isError ? (
        <ErrorState
          title="Unable to load review items"
          message="We couldn't reach the API to load recommendations."
          retry={() => void refetch()}
        />
      ) : reviewItems.length === 0 ? (
        <EmptyState
          icon={RotateCcw}
          title="Nothing to review right now"
          description="Spaced repetition and a full review queue are coming in a later phase (Phase 10). For now, this page surfaces lessons whose skill mastery has dipped below a comfortable threshold since you completed them — keep practicing and they'll show up here if it happens."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {reviewItems.map((item) => (
            <Link
              key={item.lesson.id}
              href={`/learn/${item.lesson.domain_slug}/${item.lesson.module_slug}/${item.lesson.slug}`}
              className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader>
                  <CardTitle className="text-sm">{item.lesson.title}</CardTitle>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">{item.explanation}</CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
