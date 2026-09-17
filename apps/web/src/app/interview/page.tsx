"use client";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewDashboard } from "@/components/features/interview/interview-dashboard";

export default function InterviewPage() {
  return (
    <div>
      <PageHeader
        title="Interview Prep"
        subtitle="Structured interview readiness for a Data Analyst with ~2 years of experience — technical, analytical, and behavioral rounds, all scored deterministically."
      />
      <InterviewDashboard />
    </div>
  );
}
