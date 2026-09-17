"use client";

import Link from "next/link";
import { FolderKanban } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Section } from "@/components/shared/section";
import { useProjectTemplates, useProjects } from "@/features/projects/use-projects";

import { PROJECT_STATUS_LABELS, PROJECT_STATUS_VARIANT, formatDate } from "./project-format";
import { ProjectTemplateGrid } from "./project-template-grid";

/**
 * Projects list (Phase 5 free-form shells, extended in place by Phase 8) —
 * "Start from a Template" seeds a guided, milestone-driven project; "Create
 * Project from Dataset" (still linked from the Dataset Hub/detail pages)
 * keeps producing a free-form shell. Both kinds land in the same list below,
 * each linking into the same Project Workspace.
 */
export function ProjectListPage() {
  const projectsQuery = useProjects();
  const templatesQuery = useProjectTemplates();

  return (
    <div className="flex flex-col gap-8">
      <Section
        title="Start from a Template"
        description="A guided, multi-milestone capstone project referencing SQL Lab, Python Lab, EDA, the Data Modeler, and dbt Lab."
      >
        <ProjectTemplateGrid />
      </Section>

      <Section title="Your Projects" description="Free-form projects started from a dataset, plus any template-based projects you've started.">
        {projectsQuery.isLoading ? (
          <LoadingState count={3} itemClassName="h-20" />
        ) : projectsQuery.isError ? (
          <ErrorState message="We couldn't reach the API to load your projects." retry={() => void projectsQuery.refetch()} />
        ) : !projectsQuery.data || projectsQuery.data.length === 0 ? (
          <EmptyState
            icon={FolderKanban}
            title="No projects yet"
            description='Start one from a template above, or open a dataset from the Dataset Hub and click "Create Project".'
            action={{ label: "Browse Datasets", href: "/datasets" }}
          />
        ) : (
          <ul className="flex flex-col gap-2">
            {projectsQuery.data.map((project) => {
              const template = templatesQuery.data?.find((t) => t.id === project.template_id);
              return (
                <li key={project.id} className="rounded-xl border border-border bg-card p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <Link href={`/projects/${project.id}`} className="font-medium text-foreground hover:underline">
                        {project.name}
                      </Link>
                      {project.description ? (
                        <p className="mt-1 text-sm text-muted-foreground">{project.description}</p>
                      ) : null}
                    </div>
                    <div className="flex shrink-0 flex-wrap items-center justify-end gap-1.5">
                      {template ? <Badge variant="secondary">Template: {template.title}</Badge> : null}
                      <Badge variant={PROJECT_STATUS_VARIANT[project.status]}>{PROJECT_STATUS_LABELS[project.status]}</Badge>
                    </div>
                  </div>
                  {project.notes ? <p className="mt-2 text-sm text-muted-foreground">{project.notes}</p> : null}
                  <p className="mt-2 text-xs text-muted-foreground">Updated {formatDate(project.updated_at)}</p>
                  {project.dataset_id ? (
                    <Link
                      href={`/datasets/${project.dataset_id}`}
                      className="mt-1 inline-block text-xs font-medium text-primary hover:underline"
                    >
                      View source dataset →
                    </Link>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </Section>
    </div>
  );
}
