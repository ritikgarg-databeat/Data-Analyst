"use client";

import { PageHeader } from "@/components/shared/page-header";
import { ProjectListPage } from "@/components/features/projects/project-list-page";

/**
 * Projects (Phase 5 shell extended in place by the Phase 8 Project Engine) —
 * start a guided project from one of the 8 seeded templates, or keep using
 * the free-form "Create Project from Dataset" flow linked from the Dataset
 * Hub. Both land in the same list and the same Project Workspace.
 */
export default function ProjectsPage() {
  return (
    <div>
      <PageHeader
        title="Projects"
        subtitle="Longer, multi-tool capstone projects — start from a guided template or from a dataset."
      />
      <ProjectListPage />
    </div>
  );
}
