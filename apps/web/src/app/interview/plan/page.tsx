"use client";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewPlanPage } from "@/components/features/interview/interview-plan-page";

export default function InterviewPlanRoute() {
  return (
    <div>
      <PageHeader title="My 7-Day Plan" subtitle="A personalized plan generated from your actual performance so far." />
      <InterviewPlanPage />
    </div>
  );
}
