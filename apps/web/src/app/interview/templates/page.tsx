"use client";

import { PageHeader } from "@/components/shared/page-header";
import { InterviewTemplatesCatalog } from "@/components/features/interview/interview-templates-catalog";

export default function InterviewTemplatesPage() {
  return (
    <div>
      <PageHeader
        title="Company-Style Assessments"
        subtitle="Generic interview-loop archetypes — not claims about any specific company's current hiring process."
      />
      <InterviewTemplatesCatalog />
    </div>
  );
}
