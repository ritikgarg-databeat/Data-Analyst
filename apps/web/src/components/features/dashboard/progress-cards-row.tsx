import { Award, Flame, Gauge, Sparkles } from "lucide-react";
import type { DifficultyLevel, ProgressSummary } from "@data-analyst-lab/shared";

import { AnimatedNumber } from "@/components/shared/animated-number";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";

import { ProgressCard } from "./progress-card";

const LEVEL_LABELS: Record<DifficultyLevel, string> = {
  BEGINNER: "Beginner",
  INTERMEDIATE: "Intermediate",
  ADVANCED: "Advanced",
};

interface ProgressCardsRowProps {
  summary: ProgressSummary | undefined;
  isLoading: boolean;
  isError: boolean;
  onRetry: () => void;
}

/** The dashboard's 4-card progress row: Overall Progress, Current Level, Streak, Skills Mastered. */
export function ProgressCardsRow({ summary, isLoading, isError, onRetry }: ProgressCardsRowProps) {
  if (isLoading) {
    return (
      <LoadingState count={4} className="grid-cols-2 lg:grid-cols-4" itemClassName="h-28" />
    );
  }

  if (isError) {
    return (
      <ErrorState
        title="Unable to load progress"
        message="We couldn't reach the progress summary. The rest of the dashboard is still available."
        retry={onRetry}
      />
    );
  }

  const overall = summary?.overall_progress_percent ?? 0;
  const level = summary ? LEVEL_LABELS[summary.current_level] : "Beginner";
  const streak = summary?.learning_streak_days ?? 0;
  const mastered = summary?.skills_mastered ?? 0;
  const totalSkills = summary?.total_skills ?? 0;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <ProgressCard
        icon={Gauge}
        label="Overall Progress"
        color="violet"
        value={<AnimatedNumber value={overall} format={(v) => `${Math.round(v)}%`} />}
        hint="Across all active domains"
      />
      <ProgressCard icon={Award} label="Current Level" color="amber" value={level} hint="Adapts as you master skills" />
      <ProgressCard
        icon={Flame}
        label="Learning Streak"
        color="rose"
        value={<AnimatedNumber value={streak} format={(v) => `${Math.round(v)} ${Math.round(v) === 1 ? "day" : "days"}`} />}
        hint="Consecutive days active"
      />
      <ProgressCard
        icon={Sparkles}
        label="Skills Mastered"
        color="emerald"
        value={<AnimatedNumber value={mastered} format={(v) => `${Math.round(v)} / ${totalSkills}`} />}
        hint="Mastery threshold reached"
      />
    </div>
  );
}
