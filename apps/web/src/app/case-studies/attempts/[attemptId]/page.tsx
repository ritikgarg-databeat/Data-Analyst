"use client";

import { useParams } from "next/navigation";

import { CaseWorkspace } from "@/components/features/case-studies/case-workspace";

export default function CaseWorkspacePage() {
  const params = useParams<{ attemptId: string }>();
  return <CaseWorkspace attemptId={params.attemptId} />;
}
