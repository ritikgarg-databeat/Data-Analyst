"use client";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewPrepPage } from "@/components/features/career/interview-prep-page";

export default function CareerInterviewPrepPage() {
  return (
    <div>
      <PageHeader
        title="Interview Prep"
        subtitle="The career-specific view on top of the main Interview section — job-specific plans and your behavioral story bank."
      />
      <InterviewPrepPage />
    </div>
  );
}
