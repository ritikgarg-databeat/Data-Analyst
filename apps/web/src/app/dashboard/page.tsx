"use client";

import { Sparkles } from "lucide-react";
import { motion } from "framer-motion";

import { ActivitySection } from "@/components/features/dashboard/activity-section";
import { CareerSnapshotTile } from "@/components/features/dashboard/career-snapshot-tile";
import { ContinueLearningSection } from "@/components/features/dashboard/continue-learning-section";
import { NextBestActionCard } from "@/components/features/dashboard/next-best-action-card";
import { ProgressCardsRow } from "@/components/features/dashboard/progress-cards-row";
import { RecentlyCompletedSection } from "@/components/features/dashboard/recently-completed-section";
import { SkillOverviewSection } from "@/components/features/dashboard/skill-overview-section";
import { TodaysMissionCard } from "@/components/features/dashboard/todays-mission-card";
import { WeakAreasSection } from "@/components/features/dashboard/weak-areas-section";
import { Section } from "@/components/shared/section";
import { useAuth } from "@/features/auth/auth-provider";
import { useProgressSummary } from "@/features/progress/use-progress-summary";

function personalLabTitle(name: string | undefined): string {
  const firstName = name?.trim().split(/\s+/)[0];
  return firstName ? `${firstName}'s Personal Data Lab` : "Your Personal Data Lab";
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: summary, isLoading, isError, refetch } = useProgressSummary();

  return (
    <div className="flex flex-col gap-8">
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="bg-mesh -mx-4 -mt-2 flex items-center gap-3.5 rounded-2xl px-5 py-6 sm:-mx-6 sm:px-8 lg:-mx-8"
      >
        <span className="gradient-brand glow-primary flex size-11 shrink-0 items-center justify-center rounded-xl text-white">
          <Sparkles className="size-5.5" aria-hidden="true" />
        </span>
        <div>
          <h1 className="text-gradient-brand text-2xl font-bold tracking-tight sm:text-3xl">
            {personalLabTitle(user?.name)}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Your focused space to learn, practice, build, and grow.
          </p>
        </div>
      </motion.div>

      <ProgressCardsRow summary={summary} isLoading={isLoading} isError={isError} onRetry={() => void refetch()} />
      <Section title="Continue Learning" description="Pick up right where you left off."><ContinueLearningSection items={summary?.continue_learning ?? []} /></Section>
      <Section title="Today's Mission" description="Deterministic, priority-ordered recommendations."><TodaysMissionCard /></Section>
      <Section title="Next Best Action" description="Cross-domain suggestions — interview prep, job descriptions, portfolio, and goals, not just lessons."><NextBestActionCard /></Section>
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <Section title="Recently Completed"><RecentlyCompletedSection items={summary?.recently_completed ?? []} /></Section>
        <Section title="Weak Areas"><WeakAreasSection items={summary?.weak_areas ?? []} /></Section>
      </div>
      <Section title="Career Snapshot" description="Your latest computed readiness assessment."><CareerSnapshotTile /></Section>
      <Section title="Learning Activity" description="Lessons and exercises touched over the last 14 days."><ActivitySection days={summary?.activity ?? []} /></Section>
      <Section title="Skill Overview" description="Mastery across all 12 core skill categories."><SkillOverviewSection overview={summary?.skill_overview ?? []} /></Section>
    </div>
  );
}
