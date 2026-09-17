"use client";

import Link from "next/link";
import { Compass } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ErrorState } from "@/components/shared/error-state";
import { CAREER_READINESS_LEVEL_LABELS, READINESS_DISCLAIMER } from "@/features/career/constants";
import { useLatestCareerAssessment } from "@/features/career/use-career";

/**
 * Compact "Career Snapshot" dashboard tile (Phase 12) — reuses the existing
 * readiness hook (GET /career/readiness/latest) rather than refetching
 * manually. Renders nothing until a readiness assessment has actually been
 * computed, so the dashboard never shows a hollow "0%" placeholder — but a
 * genuine fetch failure is still surfaced (never silently indistinguishable
 * from "no assessment yet"), matching NextBestActionCard's sibling pattern.
 */
export function CareerSnapshotTile() {
  const { data: assessment, isLoading, isError, refetch } = useLatestCareerAssessment();

  if (isLoading) return null;
  if (isError) {
    return (
      <ErrorState
        title="Unable to load your career snapshot"
        message="We couldn't reach the API to load your latest readiness assessment."
        retry={() => void refetch()}
      />
    );
  }
  if (!assessment) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="flex items-center gap-1.5">
            <Compass className="size-4" aria-hidden="true" />
            Career Snapshot
          </CardTitle>
          <Badge variant="outline">{CAREER_READINESS_LEVEL_LABELS[assessment.overall_readiness_level]}</Badge>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-foreground">{assessment.overall_score.toFixed(0)}</span>
          <span className="text-xs text-muted-foreground">/ 100 readiness</span>
        </div>
        <p className="text-xs text-muted-foreground">{READINESS_DISCLAIMER}</p>
        <Link href="/career/analytics" className="text-xs font-medium text-primary hover:underline">
          Open Career Analytics
        </Link>
      </CardContent>
    </Card>
  );
}
