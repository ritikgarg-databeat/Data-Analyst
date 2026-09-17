"use client";

import { PageHeader } from "@/components/shared/page-header";
import { DatasetHub } from "@/components/features/datasets/dataset-hub";

export default function DatasetsPage() {
  return (
    <div>
      <PageHeader
        title="Dataset Hub"
        subtitle="Discover, import, and profile the datasets behind your SQL, Python, and visualization practice."
      />
      <DatasetHub />
    </div>
  );
}
