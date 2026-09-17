"use client";

import { PageHeader } from "@/components/shared/page-header";
import { JobDescriptionsPage } from "@/components/features/career/job-descriptions-page";

export default function CareerJobDescriptionsPage() {
  return (
    <div>
      <PageHeader
        title="Job Descriptions"
        subtitle="Paste a real job posting to extract its requirements, find your skill gaps against it, and build a prep plan."
      />
      <JobDescriptionsPage />
    </div>
  );
}
