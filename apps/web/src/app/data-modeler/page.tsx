"use client";

import { PageHeader } from "@/components/shared/page-header";
import { ModelListPage } from "@/components/features/data-modeling/model-list-page";

export default function DataModelerPage() {
  return (
    <div>
      <PageHeader
        title="Data Modeler"
        subtitle="Design a dimensional model — tables, columns, keys, grain, and relationships — then validate it."
      />
      <ModelListPage
        modelKind="DIMENSIONAL"
        basePath="/data-modeler"
        emptyDescription="Create a model above to design a star schema — facts, dimensions, and the relationships between them."
      />
    </div>
  );
}
