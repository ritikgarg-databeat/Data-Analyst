"use client";

import { PageHeader } from "@/components/shared/page-header";
import { ProductAnalyticsWorkspace } from "@/components/features/product-analytics/product-analytics-workspace";

export default function ProductAnalyticsPage() {
  return (
    <div>
      <PageHeader
        title="Product Analytics"
        subtitle="Build a funnel and a cohort retention matrix from real event data — no spreadsheet required."
      />
      <ProductAnalyticsWorkspace />
    </div>
  );
}
