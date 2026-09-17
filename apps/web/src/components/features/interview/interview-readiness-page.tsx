"use client";

import { AlertCircle } from "lucide-react";
import type { Data, Layout } from "plotly.js";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PlotlyView } from "@/components/shared/plotly-view";
import { INTERVIEW_SECTION_TYPE_LABELS } from "@/features/interview/constants";
import { useReadiness, useReadinessHistory, useWeaknesses } from "@/features/interview/use-interview";

const GAP_TYPE_LABELS: Record<string, string> = {
  Knowledge: "Knowledge gap",
  Execution: "Execution gap",
  Reasoning: "Reasoning gap",
  Communication: "Communication gap",
  Speed: "Speed gap",
};

export function InterviewReadinessPage() {
  const readinessQuery = useReadiness();
  const historyQuery = useReadinessHistory();
  const weaknessesQuery = useWeaknesses();

  const isLoading = readinessQuery.isLoading || historyQuery.isLoading || weaknessesQuery.isLoading;
  const isError = readinessQuery.isError || historyQuery.isError || weaknessesQuery.isError;

  if (isLoading) return <LoadingState count={3} itemClassName="h-40" />;
  if (isError) {
    return (
      <ErrorState
        message="We couldn't load your readiness data."
        retry={() => {
          void readinessQuery.refetch();
          void historyQuery.refetch();
          void weaknessesQuery.refetch();
        }}
      />
    );
  }

  const history = historyQuery.data ?? [];
  const trace: Data = {
    x: history.map((h) => h.computed_at),
    y: history.map((h) => h.overall_score),
    type: "scatter",
    mode: "lines+markers",
    line: { color: "#6366f1" },
    name: "Overall Readiness",
  };
  const layout: Partial<Layout> = {
    margin: { t: 10, r: 10, b: 40, l: 40 },
    yaxis: { range: [0, 100], title: { text: "Readiness %" } },
    xaxis: { title: { text: "" } },
    height: 280,
  };

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Readiness Trend</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <EmptyState
              icon={AlertCircle}
              title="No readiness history yet"
              description="Complete an interview to start tracking your readiness over time."
            />
          ) : (
            <PlotlyView data={[trace]} layout={layout} />
          )}
        </CardContent>
      </Card>

      {readinessQuery.data && Object.keys(readinessQuery.data.breakdown).length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Breakdown by Round Type</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2">
              {Object.entries(readinessQuery.data.breakdown)
                .sort((a, b) => b[1] - a[1])
                .map(([type, score]) => (
                  <li key={type} className="flex items-center justify-between text-sm">
                    <span className="text-foreground">
                      {INTERVIEW_SECTION_TYPE_LABELS[type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ?? type}
                    </span>
                    <span className="font-medium text-foreground">{score.toFixed(0)}%</span>
                  </li>
                ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Detected Weaknesses</CardTitle>
        </CardHeader>
        <CardContent>
          {(weaknessesQuery.data ?? []).length === 0 ? (
            <EmptyState
              icon={AlertCircle}
              title="No recurring weaknesses detected yet"
              description="Weaknesses need at least 2 similar occurrences before they're flagged here."
            />
          ) : (
            <ul className="flex flex-col gap-3">
              {(weaknessesQuery.data ?? []).map((w, i) => (
                <li key={i} className="rounded-lg border border-border p-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{GAP_TYPE_LABELS[w.gap_type] ?? w.gap_type}</Badge>
                    <Badge variant="outline">
                      {INTERVIEW_SECTION_TYPE_LABELS[w.interview_type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ?? w.interview_type}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {w.occurrences}x, avg {w.average_score.toFixed(0)}%
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{w.detail}</p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
