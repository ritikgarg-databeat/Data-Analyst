"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { DataQualityWorkspace } from "@/components/features/data-quality/data-quality-workspace";

function DataQualityContent() {
  // "Data Quality" from a dataset's page deep-links here as `?dataset=<id>` to pre-select it.
  const searchParams = useSearchParams();
  return <DataQualityWorkspace initialDatasetId={searchParams.get("dataset") ?? undefined} />;
}

export default function DataQualityPage() {
  return (
    <div>
      <PageHeader
        title="Data Quality Lab"
        subtitle="Build completeness, uniqueness, validity, consistency, and freshness rules — and run them for real against your data."
      />
      <Suspense fallback={<LoadingState count={1} itemClassName="h-96" />}>
        <DataQualityContent />
      </Suspense>
    </div>
  );
}
