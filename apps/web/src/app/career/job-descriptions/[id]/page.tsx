"use client";

import { useParams } from "next/navigation";

import { PageHeader } from "@/components/shared/page-header";
import { JobDescriptionDetail } from "@/components/features/career/job-description-detail";

export default function JobDescriptionDetailPage() {
  const params = useParams<{ id: string }>();
  return (
    <div>
      <PageHeader
        title="Job Description"
        subtitle="Extract requirements, see your skill gaps, analyze readiness, and build a preparation plan for this specific posting."
      />
      <JobDescriptionDetail jobDescriptionId={params.id} />
    </div>
  );
}
