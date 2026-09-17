import type { MasteryLevel, UserSkill } from "@data-analyst-lab/shared";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const MASTERY_LEVEL_VARIANT: Record<MasteryLevel, BadgeProps["variant"]> = {
  BEGINNER: "outline",
  DEVELOPING: "secondary",
  INTERMEDIATE: "secondary",
  STRONG: "default",
  MASTERED: "success",
};

const MASTERY_LEVEL_LABEL: Record<MasteryLevel, string> = {
  BEGINNER: "Beginner",
  DEVELOPING: "Developing",
  INTERMEDIATE: "Intermediate",
  STRONG: "Strong",
  MASTERED: "Mastered",
};

function formatRelativeDate(iso: string): string {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 30) return `${days} days ago`;
  const months = Math.floor(days / 30);
  return months === 1 ? "1 month ago" : `${months} months ago`;
}

interface SkillListCardProps {
  userSkill: UserSkill;
}

export function SkillListCard({ userSkill }: SkillListCardProps) {
  const { skill, mastery_score, mastery_level, questions_attempted, questions_correct, last_practiced_at } =
    userSkill;

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-2">
        <div className="space-y-1">
          <CardTitle className="text-sm">{skill.name}</CardTitle>
          {skill.description ? (
            <CardDescription className="line-clamp-2">{skill.description}</CardDescription>
          ) : null}
        </div>
        <Badge variant={MASTERY_LEVEL_VARIANT[mastery_level]}>{MASTERY_LEVEL_LABEL[mastery_level]}</Badge>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Mastery</span>
          <span>{Math.round(mastery_score)}%</span>
        </div>
        <Progress value={mastery_score} aria-label={`${skill.name} mastery: ${Math.round(mastery_score)}%`} />
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {questions_correct}/{questions_attempted} correct
          </span>
          <span>{last_practiced_at ? formatRelativeDate(last_practiced_at) : "Not practiced yet"}</span>
        </div>
      </CardContent>
    </Card>
  );
}
