import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

interface SkillCategoryCardProps {
  label: string;
  /** Average mastery percent (0-100). Defaults to 0 when no data is available yet. */
  masteryPercent?: number;
  skillCount?: number;
}

/** Card for one of the 12 skill categories, shown on the dashboard and /skills page. */
export function SkillCategoryCard({ label, masteryPercent = 0, skillCount }: SkillCategoryCardProps) {
  const rounded = Math.round(masteryPercent);
  return (
    <Card>
      <CardHeader className="pb-0">
        <CardTitle className="text-sm">{label}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{rounded}% mastery</span>
          {typeof skillCount === "number" ? <span>{skillCount} skills</span> : null}
        </div>
        <Progress value={rounded} aria-label={`${label} mastery: ${rounded}%`} />
      </CardContent>
    </Card>
  );
}
