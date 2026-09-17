"use client";

import { PageHeader } from "@/components/shared/page-header";
import { SkillGapsPage } from "@/components/features/career/skill-gaps-page";

export default function CareerSkillGapsPage() {
  return (
    <div>
      <PageHeader
        title="Skill Gaps"
        subtitle="Your full skill matrix — mastery, evidence, and practice history — with gaps against your primary target role highlighted."
      />
      <SkillGapsPage />
    </div>
  );
}
