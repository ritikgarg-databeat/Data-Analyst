"use client";

import { PageHeader } from "@/components/shared/page-header";
import { ModelListPage } from "@/components/features/data-modeling/model-list-page";

export default function ArchitecturePage() {
  return (
    <div>
      <PageHeader
        title="Architecture Diagram Builder"
        subtitle="Sketch a system architecture — sources, storage, warehouses, transforms, services, and how data flows between them."
      />
      <ModelListPage
        modelKind="ARCHITECTURE"
        basePath="/architecture"
        emptyDescription="Create a diagram above to map out a data architecture — where data lives and how it flows."
      />
    </div>
  );
}
