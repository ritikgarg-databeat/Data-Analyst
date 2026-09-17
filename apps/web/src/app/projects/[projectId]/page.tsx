"use client";

import { useParams } from "next/navigation";

import { ProjectWorkspace } from "@/components/features/projects/project-workspace";

export default function ProjectWorkspacePage() {
  const params = useParams<{ projectId: string }>();
  return <ProjectWorkspace projectId={params.projectId} />;
}
