"use client";

import { PageHeader } from "@/components/shared/page-header";
import { CareerAnalyticsPage } from "@/components/features/career/career-analytics-page";

export default function CareerAnalyticsPageRoute() {
  return (
    <div>
      <PageHeader
        title="Career Analytics"
        subtitle="Readiness trend, weekly review, progress timeline, achievements, your career knowledge base, and a downloadable career report."
      />
      <CareerAnalyticsPage />
    </div>
  );
}
