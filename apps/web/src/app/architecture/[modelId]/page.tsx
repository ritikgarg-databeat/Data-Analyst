"use client";

import { useParams } from "next/navigation";

import { ModelCanvas } from "@/components/features/data-modeling/model-canvas";

export default function ArchitectureEditorPage() {
  const params = useParams<{ modelId: string }>();
  return <ModelCanvas modelId={params.modelId} modelKind="ARCHITECTURE" basePath="/architecture" />;
}
