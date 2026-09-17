"use client";

import { useParams } from "next/navigation";

import { ModelCanvas } from "@/components/features/data-modeling/model-canvas";

export default function PipelineEditorPage() {
  const params = useParams<{ modelId: string }>();
  return <ModelCanvas modelId={params.modelId} modelKind="PIPELINE" basePath="/pipeline" />;
}
