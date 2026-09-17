"use client";

import { PageHeader } from "@/components/shared/page-header";
import { CareerDashboard } from "@/components/features/career/career-dashboard";

export default function CareerPage() {
  return (
    <div>
      <PageHeader
        title="Career"
        subtitle="Am I ready for a Data Analyst role, what are my gaps, and how do I prepare for a specific job? Every readiness number here is a platform estimate — never a hiring guarantee."
      />
      <CareerDashboard />
    </div>
  );
}
