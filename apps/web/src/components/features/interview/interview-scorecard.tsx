"use client";

import type { InterviewScore } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

function toneClass(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400";
  if (score >= 60) return "text-amber-600 dark:text-amber-400";
  return "text-rose-600 dark:text-rose-400";
}

/** The Interview Scorecard (spec section 38) — overall readiness-relevant
 * score plus the 6-dimension breakdown, reused wherever a completed
 * interview's score needs to be shown (review page, recent scores, etc). */
export function InterviewScorecard({ score }: { score: InterviewScore }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Scorecard</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div>
          <p className={`text-3xl font-semibold ${toneClass(score.overall)}`}>{score.overall.toFixed(0)}%</p>
          <p className="text-xs text-muted-foreground">Overall</p>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {score.dimensions
            .filter((d) => d.question_count > 0)
            .map((dimension) => (
              <div key={dimension.dimension}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="text-foreground">{dimension.dimension}</span>
                  <span className="font-medium text-foreground">{dimension.score.toFixed(0)}%</span>
                </div>
                <Progress value={dimension.score} />
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}
