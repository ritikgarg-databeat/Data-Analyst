"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useInterviewTemplatesAdmin, useUpdateInterviewTemplateAdmin } from "@/features/interview/use-interview";

export function InterviewTemplateAdminPanel() {
  const { data: templates, isLoading, isError, refetch } = useInterviewTemplatesAdmin();
  const updateTemplate = useUpdateInterviewTemplateAdmin();

  if (isLoading) return <LoadingState count={4} itemClassName="h-12" />;
  if (isError) {
    return <ErrorState title="Unable to load assessment templates" message="We couldn't reach the API." retry={() => void refetch()} />;
  }

  return (
    <div className="space-y-4">
      <p className="rounded-lg border border-border bg-muted/30 px-4 py-2 text-xs text-muted-foreground">
        Assessment templates (mock interviews and company-style structures) are authored in{" "}
        <code>content/interview/templates/</code> — edit those files and re-sync to change sections or scoring
        weights. Here you can only activate or deactivate one.
      </p>

      <div className="divide-y divide-border rounded-lg border border-border">
        {(templates ?? []).map((item) => (
          <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                {item.title} <span className="text-xs text-muted-foreground">({item.slug})</span>
              </p>
              <p className="text-xs text-muted-foreground">
                {item.target_profile} · {item.section_count} section{item.section_count === 1 ? "" : "s"}
              </p>
            </div>
            <div className="flex items-center gap-1">
              <Badge variant={item.is_active ? "success" : "outline"}>{item.is_active ? "Active" : "Inactive"}</Badge>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => updateTemplate.mutate({ id: item.id, is_active: !item.is_active })}
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
