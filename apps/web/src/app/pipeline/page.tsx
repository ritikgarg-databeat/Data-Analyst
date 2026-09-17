"use client";

import { PageHeader } from "@/components/shared/page-header";
import { ModelListPage } from "@/components/features/data-modeling/model-list-page";
import { PipelineStageReference } from "@/components/features/data-modeling/pipeline-stage-reference";

export default function PipelinePage() {
  return (
    <div>
      <PageHeader
        title="Pipeline Playground"
        subtitle="Learn the generic shape of a pipeline, then design your own — stages, dependencies, and where they can break."
      />
      <div className="mb-6">
        <PipelineStageReference />
      </div>
      <ModelListPage
        modelKind="PIPELINE"
        basePath="/pipeline"
        emptyDescription="Create a pipeline above to design stages and dependencies — a cycle here is a real error, since a pipeline must be a DAG."
      />
    </div>
  );
}
