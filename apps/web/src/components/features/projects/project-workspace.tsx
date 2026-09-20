"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { useProject, useProjectTemplates } from "@/features/projects/use-projects";
import { cn } from "@/lib/utils";

import { ProjectAnalysisTab } from "./project-analysis-tab";
import { ProjectArtifactsTab } from "./project-artifacts-tab";
import { ProjectDataModelTab } from "./project-data-model-tab";
import { ProjectDatasetsTab } from "./project-datasets-tab";
import { ProjectDocumentationTab } from "./project-documentation-tab";
import { PROJECT_STATUS_LABELS, PROJECT_STATUS_VARIANT } from "./project-format";
import { ProjectMilestonesTab } from "./project-milestones-tab";
import { ProjectOverviewTab } from "./project-overview-tab";
import { ProjectPresentationTab } from "./project-presentation-tab";
import { ProjectSubmissionTab } from "./project-submission-tab";

type TabKey =
  | "overview"
  | "milestones"
  | "datasets"
  | "analysis"
  | "artifacts"
  | "data-model"
  | "documentation"
  | "presentation"
  | "submission";

const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "milestones", label: "Milestones" },
  { key: "datasets", label: "Datasets" },
  { key: "analysis", label: "Analysis" },
  { key: "artifacts", label: "Artifacts" },
  { key: "data-model", label: "Data Model & dbt" },
  { key: "documentation", label: "Documentation" },
  { key: "presentation", label: "Presentation" },
  { key: "submission", label: "Submission" },
];

/**
 * The Project Workspace (Phase 8) — a single long-lived, multi-session
 * project's working page. Covers both the free-form shell (Phase 5) and a
 * template-based project (Phase 8, has `template_id` set and seeded
 * milestones/rubric). Sections are laid out as tabs since this is a
 * long-lived workspace revisited across many sessions.
 */
export function ProjectWorkspace({ projectId }: { projectId: string }) {
  const projectQuery = useProject(projectId);
  const templatesQuery = useProjectTemplates();
  const [tab, setTab] = useState<TabKey>("overview");

  if (projectQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-96" />;
  }

  if (projectQuery.isError || !projectQuery.data) {
    return (
      <ErrorState
        title="Unable to load this project"
        message="We couldn't reach the API, or this project doesn't exist."
        retry={() => void projectQuery.refetch()}
      />
    );
  }

  const project = projectQuery.data;
  const template = templatesQuery.data?.find((t) => t.id === project.template_id);

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title={project.name}
        subtitle={project.objective ?? project.description ?? undefined}
        action={
          <div className="flex items-center gap-2">
            <Badge variant={PROJECT_STATUS_VARIANT[project.status]}>{PROJECT_STATUS_LABELS[project.status]}</Badge>
            <Button variant="outline" size="sm" asChild>
              <Link href="/projects">
                <ArrowLeft className="size-4" aria-hidden="true" />
                All Projects
              </Link>
            </Button>
          </div>
        }
      />

      <div className="flex max-w-full gap-1.5 overflow-x-auto border-b border-border scrollbar-thin" role="tablist" aria-label="Project workspace sections">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "shrink-0 rounded-t-md px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors",
              tab === t.key
                ? "border-b-2 border-primary text-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {tab === "overview" ? <ProjectOverviewTab project={project} template={template} /> : null}
        {tab === "milestones" ? <ProjectMilestonesTab project={project} /> : null}
        {tab === "datasets" ? <ProjectDatasetsTab project={project} /> : null}
        {tab === "analysis" ? <ProjectAnalysisTab project={project} /> : null}
        {tab === "artifacts" ? <ProjectArtifactsTab project={project} /> : null}
        {tab === "data-model" ? <ProjectDataModelTab project={project} /> : null}
        {tab === "documentation" ? <ProjectDocumentationTab project={project} /> : null}
        {tab === "presentation" ? <ProjectPresentationTab project={project} /> : null}
        {tab === "submission" ? <ProjectSubmissionTab project={project} template={template} /> : null}
      </div>
    </div>
  );
}
