"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LayoutTemplate } from "lucide-react";
import type { ProjectTemplate } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useProjectTemplates, useStartProjectFromTemplate } from "@/features/projects/use-projects";

import { formatEnumLabel } from "./project-format";

function excerpt(text: string | null, max = 160): string {
  if (!text) return "";
  const trimmed = text.trim().replace(/\s+/g, " ");
  return trimmed.length > max ? `${trimmed.slice(0, max - 1)}…` : trimmed;
}

function TemplateCard({ template }: { template: ProjectTemplate }) {
  const router = useRouter();
  const startProject = useStartProjectFromTemplate();
  const [error, setError] = useState(false);

  function handleStart() {
    setError(false);
    startProject.mutate(
      { template_slug: template.slug },
      {
        onSuccess: (project) => router.push(`/projects/${project.id}`),
        onError: () => setError(true),
      },
    );
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">{formatEnumLabel(template.category)}</Badge>
        {template.estimated_hours ? <Badge variant="secondary">~{template.estimated_hours}h</Badge> : null}
      </div>
      <div>
        <p className="font-medium text-foreground">{template.title}</p>
        <p className="mt-1 text-sm text-muted-foreground">{excerpt(template.business_context ?? template.objective)}</p>
      </div>
      {template.tags.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {template.tags.slice(0, 5).map((tag) => (
            <Badge key={tag} variant="outline" className="text-[10px]">
              {tag}
            </Badge>
          ))}
        </div>
      ) : null}
      <Button size="sm" onClick={handleStart} disabled={startProject.isPending} className="mt-auto self-start">
        {startProject.isPending ? "Starting…" : "Start Project"}
      </Button>
      {error ? <p className="text-xs text-destructive">Couldn&apos;t start this project. Try again.</p> : null}
    </div>
  );
}

/** "Start from a Template" grid (Phase 8) — the 8 seeded ProjectTemplates. Starting one
 * calls POST /projects/from-template, which instantiates the project's milestones[], then
 * routes straight into its workspace. */
export function ProjectTemplateGrid() {
  const templatesQuery = useProjectTemplates();

  if (templatesQuery.isLoading) return <LoadingState count={4} itemClassName="h-48" />;
  if (templatesQuery.isError) {
    return (
      <ErrorState
        message="We couldn't reach the API to load project templates."
        retry={() => void templatesQuery.refetch()}
      />
    );
  }
  if (!templatesQuery.data || templatesQuery.data.length === 0) {
    return (
      <EmptyState
        icon={LayoutTemplate}
        title="No project templates yet"
        description="Guided, multi-milestone capstone projects will show up here once templates are published."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {templatesQuery.data.map((template) => (
        <TemplateCard key={template.id} template={template} />
      ))}
    </div>
  );
}
