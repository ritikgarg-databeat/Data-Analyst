"use client";

import { useRouter } from "next/navigation";
import { ListTree } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_SECTION_TYPE_LABELS } from "@/features/interview/constants";
import { useCreateInterview, useInterviewTemplates } from "@/features/interview/use-interview";

export function InterviewTemplatesCatalog() {
  const templatesQuery = useInterviewTemplates();
  const createInterview = useCreateInterview();
  const router = useRouter();

  if (templatesQuery.isLoading) return <LoadingState count={4} itemClassName="h-40" />;
  if (templatesQuery.isError) {
    return <ErrorState message="We couldn't load company-style assessments." retry={() => void templatesQuery.refetch()} />;
  }

  const templates = templatesQuery.data ?? [];
  if (templates.length === 0) {
    return <EmptyState icon={ListTree} title="No assessment templates yet" description="Check back soon." />;
  }

  function handleStart(templateSlug: string) {
    createInterview.mutate(
      { mode: "COMPANY_STYLE", template_slug: templateSlug },
      { onSuccess: (interview) => router.push(`/interview/session/${interview.id}`) },
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {templates.map((template) => {
        const totalMinutes = template.sections.reduce((sum, s) => sum + s.duration_minutes, 0);
        return (
          <Card key={template.id}>
            <CardHeader>
              <CardTitle>{template.title}</CardTitle>
              <p className="text-xs text-muted-foreground">{template.target_profile}</p>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {template.description ? <p className="text-sm text-muted-foreground">{template.description}</p> : null}
              <div className="flex flex-wrap gap-1.5">
                {template.sections.map((section, i) => (
                  <Badge key={i} variant="outline">
                    {INTERVIEW_SECTION_TYPE_LABELS[section.interview_type as keyof typeof INTERVIEW_SECTION_TYPE_LABELS] ??
                      section.interview_type}{" "}
                    · {section.duration_minutes}m
                  </Badge>
                ))}
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-xs text-muted-foreground">{totalMinutes} min total</span>
                <Button size="sm" onClick={() => handleStart(template.slug)} disabled={createInterview.isPending}>
                  Start
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
