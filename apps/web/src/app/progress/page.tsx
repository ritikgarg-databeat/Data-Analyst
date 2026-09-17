"use client";

import { ActivitySection } from "@/components/features/dashboard/activity-section";
import { RecentlyCompletedSection } from "@/components/features/dashboard/recently-completed-section";
import { SkillOverviewSection } from "@/components/features/dashboard/skill-overview-section";
import { WeakAreasSection } from "@/components/features/dashboard/weak-areas-section";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Section } from "@/components/shared/section";
import { Progress } from "@/components/ui/progress";
import { useProgressSummary } from "@/features/progress/use-progress-summary";

export default function ProgressPage() {
  const { data: summary, isLoading, isError, refetch } = useProgressSummary();

  if (isLoading) {
    return <LoadingState count={4} itemClassName="h-32" />;
  }
  if (isError || !summary) {
    return (
      <ErrorState
        title="Unable to load progress"
        message="We couldn't reach the API to load your progress."
        retry={() => void refetch()}
      />
    );
  }

  return (
    <div>
      <PageHeader
        title="Progress"
        subtitle="A detailed view of your mastery, history, and momentum over time."
      />

      <div className="mb-8 max-w-md space-y-1">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>Overall progress</span>
          <span>{Math.round(summary.overall_progress_percent)}%</span>
        </div>
        <Progress value={summary.overall_progress_percent} />
        <p className="pt-1 text-xs text-muted-foreground">
          Level: {summary.current_level.charAt(0) + summary.current_level.slice(1).toLowerCase()} ·{" "}
          {summary.learning_streak_days}-day streak · {summary.skills_mastered}/{summary.total_skills} skills
          mastered
        </p>
      </div>

      <Section
        title="Learning Activity"
        description="Lessons and exercises touched over the last 14 days."
        className="mb-8"
      >
        <ActivitySection days={summary.activity} size="large" />
      </Section>

      <div className="mb-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <Section title="Recently Completed">
          <RecentlyCompletedSection items={summary.recently_completed} />
        </Section>
        <Section title="Weak Areas">
          <WeakAreasSection items={summary.weak_areas} />
        </Section>
      </div>

      <Section title="Skill Overview" description="Mastery across all 12 core skill categories.">
        <SkillOverviewSection overview={summary.skill_overview} />
      </Section>
    </div>
  );
}
