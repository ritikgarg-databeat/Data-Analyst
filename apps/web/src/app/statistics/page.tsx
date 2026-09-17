"use client";

import { PageHeader } from "@/components/shared/page-header";
import { StatisticsWorkspace } from "@/components/features/statistics/statistics-workspace";

export default function StatisticsPage() {
  return (
    <div>
      <PageHeader
        title="Statistics"
        subtitle="Descriptive statistics, hypothesis testing, correlation, and regression — computed for real, with a test-selection assistant to help you pick the right tool."
      />
      <StatisticsWorkspace />
    </div>
  );
}
