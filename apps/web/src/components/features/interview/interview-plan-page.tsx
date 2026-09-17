"use client";

import Link from "next/link";
import { CalendarDays, MessagesSquare, RotateCcw, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_SECTION_TYPE_LABELS } from "@/features/interview/constants";
import { useGenerateInterviewPlan, useInterviewPlan } from "@/features/interview/use-interview";
import { useExplainPlan } from "@/features/ai/use-ai";

const TASK_ICON: Record<string, typeof CalendarDays> = {
  PRACTICE: Sparkles,
  MOCK_INTERVIEW: MessagesSquare,
  REVIEW: RotateCcw,
};

export function InterviewPlanPage() {
  const planQuery = useInterviewPlan();
  const generatePlan = useGenerateInterviewPlan();
  const explainPlan = useExplainPlan();

  if (planQuery.isLoading) return <LoadingState count={3} itemClassName="h-24" />;
  if (planQuery.isError) {
    return <ErrorState message="We couldn't load your plan." retry={() => void planQuery.refetch()} />;
  }

  const plan = planQuery.data;
  const explanationByDay = new Map(
    (explainPlan.data?.day_explanations ?? []).map((entry) => [entry.day_number, entry.why]),
  );

  return (
    <div className="flex flex-col gap-5">
      <div className="flex justify-end gap-2">
        {plan ? (
          <Button
            variant="outline"
            onClick={() => explainPlan.mutate({ plan_id: plan.id })}
            disabled={explainPlan.isPending}
          >
            <Sparkles className="size-4" aria-hidden="true" />
            {explainPlan.isPending ? "Explaining..." : "Explain with AI"}
          </Button>
        ) : null}
        <Button onClick={() => generatePlan.mutate()} disabled={generatePlan.isPending}>
          <Sparkles className="size-4" aria-hidden="true" />
          {plan ? "Regenerate Plan" : "Generate My 7-Day Plan"}
        </Button>
      </div>

      {!plan ? (
        <EmptyState
          icon={CalendarDays}
          title="No plan yet"
          description="Generate a personalized 7-day plan based on your actual performance so far."
        />
      ) : (
        <div className="flex flex-col gap-3">
          {plan.days.map((day) => {
            const Icon = TASK_ICON[day.task_type] ?? Sparkles;
            return (
              <Card key={day.day_number}>
                <CardHeader>
                  <div className="flex items-center justify-between gap-3">
                    <CardTitle className="flex items-center gap-2">
                      <Icon className="size-4 text-primary" aria-hidden="true" />
                      Day {day.day_number}: {day.title}
                    </CardTitle>
                    {day.task_ref ? (
                      <Badge variant="outline">
                        {INTERVIEW_SECTION_TYPE_LABELS[day.task_ref as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ?? day.task_ref}
                      </Badge>
                    ) : null}
                  </div>
                </CardHeader>
                <CardContent className="flex flex-col gap-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm text-muted-foreground">{day.description}</p>
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/interview">Start</Link>
                    </Button>
                  </div>
                  {explanationByDay.has(day.day_number) ? (
                    <p className="rounded-md border border-border bg-muted/40 p-2 text-xs text-foreground">
                      <span className="font-medium">Why: </span>
                      {explanationByDay.get(day.day_number)}
                    </p>
                  ) : null}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
