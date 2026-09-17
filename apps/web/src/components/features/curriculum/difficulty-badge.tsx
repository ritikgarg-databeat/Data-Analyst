import type { DifficultyLevel } from "@data-analyst-lab/shared";

import { Badge, type BadgeProps } from "@/components/ui/badge";

const DIFFICULTY_VARIANT: Record<DifficultyLevel, BadgeProps["variant"]> = {
  BEGINNER: "outline",
  INTERMEDIATE: "secondary",
  ADVANCED: "default",
};

const DIFFICULTY_LABEL: Record<DifficultyLevel, string> = {
  BEGINNER: "Beginner",
  INTERMEDIATE: "Intermediate",
  ADVANCED: "Advanced",
};

interface DifficultyBadgeProps {
  difficulty: DifficultyLevel;
  className?: string;
}

export function DifficultyBadge({ difficulty, className }: DifficultyBadgeProps) {
  return (
    <Badge variant={DIFFICULTY_VARIANT[difficulty]} className={className}>
      {DIFFICULTY_LABEL[difficulty]}
    </Badge>
  );
}
