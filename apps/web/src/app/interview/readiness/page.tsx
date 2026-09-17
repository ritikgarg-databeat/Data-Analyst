"use client";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewReadinessPage } from "@/components/features/interview/interview-readiness-page";

export default function InterviewReadinessRoute() {
  return (
    <div>
      <PageHeader title="Readiness Trend" subtitle="How your overall readiness has moved over time, and what's currently holding it back." />
      <InterviewReadinessPage />
    </div>
  );
}
