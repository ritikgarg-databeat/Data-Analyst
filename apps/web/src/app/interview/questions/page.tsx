"use client";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewQuestionCatalog } from "@/components/features/interview/interview-question-catalog";

export default function InterviewQuestionsPage() {
  return (
    <div>
      <PageHeader title="Question Bank" subtitle="Search and filter the full interview question bank, and bookmark ones to revisit." />
      <InterviewQuestionCatalog />
    </div>
  );
}
