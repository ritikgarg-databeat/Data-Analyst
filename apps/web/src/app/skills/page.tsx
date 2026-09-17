"use client";

import { Sparkles } from "lucide-react";
import { SKILL_CATEGORY_LABELS, SKILL_CATEGORY_ORDER } from "@data-analyst-lab/shared";
import type { SkillCategory, UserSkill } from "@data-analyst-lab/shared";

import { SkillListCard } from "@/components/features/skills/skill-list-card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Section } from "@/components/shared/section";
import { useSkillMastery } from "@/features/skills/use-skill-mastery";

function groupByCategory(userSkills: UserSkill[]): Map<SkillCategory, UserSkill[]> {
  const groups = new Map<SkillCategory, UserSkill[]>();
  for (const userSkill of userSkills) {
    const existing = groups.get(userSkill.skill.category);
    if (existing) {
      existing.push(userSkill);
    } else {
      groups.set(userSkill.skill.category, [userSkill]);
    }
  }
  return groups;
}

export default function SkillsPage() {
  const { data: userSkills, isLoading, isError, refetch } = useSkillMastery();

  const grouped = userSkills ? groupByCategory(userSkills) : new Map<SkillCategory, UserSkill[]>();

  return (
    <div>
      <PageHeader
        title="Skills"
        subtitle="Every skill tracked by the platform, grouped by category, with mastery from your graded exercise and assessment history."
      />

      {isLoading ? (
        <LoadingState count={4} itemClassName="h-40" />
      ) : isError ? (
        <ErrorState
          title="Unable to load skills"
          message="We couldn't reach the API to load skill mastery."
          retry={() => void refetch()}
        />
      ) : !userSkills || userSkills.length === 0 ? (
        <EmptyState
          icon={Sparkles}
          title="No skills yet"
          description="The skill catalog will appear here once skills are seeded on the backend."
        />
      ) : (
        <div className="flex flex-col gap-8">
          {SKILL_CATEGORY_ORDER.filter((category) => grouped.has(category)).map((category) => (
            <Section key={category} title={SKILL_CATEGORY_LABELS[category]}>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {grouped.get(category)!.map((userSkill) => (
                  <SkillListCard key={userSkill.skill.id} userSkill={userSkill} />
                ))}
              </div>
            </Section>
          ))}
        </div>
      )}
    </div>
  );
}
