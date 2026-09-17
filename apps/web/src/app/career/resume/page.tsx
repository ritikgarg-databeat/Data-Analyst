"use client";

import { PageHeader } from "@/components/shared/page-header";
import { ResumePage } from "@/components/features/career/resume-page";

export default function CareerResumePage() {
  return (
    <div>
      <PageHeader
        title="Resume"
        subtitle="Manage resume versions, extract quoted skill evidence, get a deterministic quality review, and check gaps against a target role."
      />
      <ResumePage />
    </div>
  );
}
