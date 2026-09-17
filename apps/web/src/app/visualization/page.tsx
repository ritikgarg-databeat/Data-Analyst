"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { PageHeader } from "@/components/shared/page-header";
import { LoadingState } from "@/components/shared/loading-state";
import { VisualizationWorkspace } from "@/components/features/charts/visualization-workspace";

function VisualizationContent() {
  const searchParams = useSearchParams();
  const datasetId = searchParams.get("dataset") ?? undefined;
  return <VisualizationWorkspace initialDatasetId={datasetId} />;
}

export default function VisualizationPage() {
  return (
    <div>
      <PageHeader
        title="Visualization"
        subtitle="Build charts with a point-and-click builder, get chart-type recommendations, and turn charts into insights."
      />
      <Suspense fallback={<LoadingState count={1} itemClassName="h-96" />}>
        <VisualizationContent />
      </Suspense>
    </div>
  );
}
