import { SKILL_CATEGORY_LABELS, SKILL_CATEGORY_ORDER } from "@data-analyst-lab/shared";
import type { SkillCategoryOverview } from "@data-analyst-lab/shared";

import { SkillCategoryCard } from "@/components/features/skills/skill-category-card";

interface SkillOverviewSectionProps {
  overview: SkillCategoryOverview[];
}

/** Grid of all 12 skill categories, showing 0% when no overview data is available yet. */
export function SkillOverviewSection({ overview }: SkillOverviewSectionProps) {
  const byCategory = new Map(overview.map((entry) => [entry.category, entry]));

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {SKILL_CATEGORY_ORDER.map((category) => {
        const entry = byCategory.get(category);
        return (
          <SkillCategoryCard
            key={category}
            label={SKILL_CATEGORY_LABELS[category]}
            masteryPercent={entry?.average_mastery ?? 0}
            skillCount={entry?.skill_count}
          />
        );
      })}
    </div>
  );
}
