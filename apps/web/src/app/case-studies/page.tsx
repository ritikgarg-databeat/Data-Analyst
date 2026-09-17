"use client";

import { PageHeader } from "@/components/shared/page-header";
import { CaseLibrary } from "@/components/features/case-studies/case-library";

export default function CaseStudiesPage() {
  return (
    <div>
      <PageHeader
        title="Case Studies"
        subtitle="Realistic, ambiguous business problems that mirror on-the-job analyst work — the platform never reveals the answer upfront."
      />
      <CaseLibrary />
    </div>
  );
}
