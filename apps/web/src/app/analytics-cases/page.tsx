import { PageHeader } from "@/components/shared/page-header";
import { CaseLibrary } from "@/components/features/analytics-cases/case-library";

export default function AnalyticsCasesPage() {
  return (
    <div>
      <PageHeader
        title="Analytics Cases"
        subtitle="Business and product analytics case studies — framed with real stakeholders, constraints, and rubric-based evaluation."
      />
      <CaseLibrary />
    </div>
  );
}
