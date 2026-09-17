"use client";

import { useParams } from "next/navigation";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewQuestionDetailView } from "@/components/features/interview/interview-question-detail";

export default function InterviewQuestionDetailPage() {
  const params = useParams<{ slug: string }>();
  return (
    <div>
      <PageHeader title="Question Detail" />
      <InterviewQuestionDetailView slug={params.slug} />
    </div>
  );
}
