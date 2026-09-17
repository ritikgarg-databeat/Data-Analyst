"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_QUESTION_TYPE_LABELS } from "@/features/interview/constants";
import { useInterviewQuestionsAdmin, useUpdateInterviewQuestionAdmin } from "@/features/interview/use-interview";

export function InterviewQuestionAdminPanel() {
  const { data: questions, isLoading, isError, refetch } = useInterviewQuestionsAdmin();
  const updateQuestion = useUpdateInterviewQuestionAdmin();

  if (isLoading) return <LoadingState count={6} itemClassName="h-12" />;
  if (isError) {
    return <ErrorState title="Unable to load interview questions" message="We couldn't reach the API." retry={() => void refetch()} />;
  }

  return (
    <div className="space-y-4">
      <p className="rounded-lg border border-border bg-muted/30 px-4 py-2 text-xs text-muted-foreground">
        Interview questions are thin wrappers authored in <code>content/interview/questions/</code>, each pointing at
        an existing exercise — edit those files and re-sync to change the underlying question. Here you can only
        activate or deactivate one.
      </p>

      <div className="divide-y divide-border rounded-lg border border-border">
        {(questions ?? []).map((item) => (
          <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                {item.slug} <span className="text-xs text-muted-foreground">→ {item.exercise_slug}</span>
              </p>
              <p className="text-xs text-muted-foreground">
                {INTERVIEW_QUESTION_TYPE_LABELS[item.interview_type]}
                {item.time_limit_seconds ? ` · ${Math.round(item.time_limit_seconds / 60)} min` : " · Untimed"}
              </p>
            </div>
            <div className="flex items-center gap-1">
              <Badge variant={item.is_active ? "success" : "outline"}>{item.is_active ? "Active" : "Inactive"}</Badge>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => updateQuestion.mutate({ id: item.id, is_active: !item.is_active })}
              >
                {item.is_active ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
