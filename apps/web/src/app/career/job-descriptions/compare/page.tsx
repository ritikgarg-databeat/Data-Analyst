"use client";

import { PageHeader } from "@/components/shared/page-header";
import { JobDescriptionsComparePage } from "@/components/features/career/job-descriptions-compare-page";

export default function CareerJobDescriptionsComparePage() {
  return (
    <div>
      <PageHeader
        title="Compare Job Descriptions"
        subtitle="See your readiness and must-have gaps side by side across two or more saved postings."
      />
      <JobDescriptionsComparePage />
    </div>
  );
}
