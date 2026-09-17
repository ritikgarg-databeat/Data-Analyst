"use client";

import { useParams } from "next/navigation";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewReviewPage } from "@/components/features/interview/interview-review-page";

export default function InterviewSessionReviewPage() {
  const params = useParams<{ id: string }>();
  return (
    <div>
      <PageHeader title="Interview Review" subtitle="Your answers, the correct answers, and what to review next." />
      <InterviewReviewPage interviewId={params.id} />
    </div>
  );
}
