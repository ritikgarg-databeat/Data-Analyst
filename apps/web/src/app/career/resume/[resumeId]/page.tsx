"use client";

import { useParams } from "next/navigation";

import { PageHeader } from "@/components/shared/page-header";
import { ResumeDetail } from "@/components/features/career/resume-detail-page";

export default function CareerResumeDetailPage() {
  const params = useParams<{ resumeId: string }>();
  return (
    <div>
      <PageHeader title="Resume Detail" subtitle="Manage versions, extract evidence, review quality, and check role gaps." />
      <ResumeDetail resumeId={params.resumeId} />
    </div>
  );
}
