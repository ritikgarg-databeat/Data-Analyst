"use client";

import { PageHeader } from "@/components/shared/page-header";
import { MyInterviewReviewPage } from "@/components/features/interview/my-interview-review-page";

export default function InterviewReviewRoute() {
  return (
    <div>
      <PageHeader title="My Interview Review" subtitle="Bookmarked questions, notes, and what's due for spaced review." />
      <MyInterviewReviewPage />
    </div>
  );
}
