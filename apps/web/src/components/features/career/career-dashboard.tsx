"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Briefcase,
  Compass,
  FileBadge,
  FileText,
  LayoutGrid,
  Mic,
  Puzzle,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { CareerCoachPanel } from "./career-coach-panel";
import {
  CAREER_MILESTONE_TYPE_LABELS,
  CAREER_READINESS_LEVEL_LABELS,
  READINESS_DISCLAIMER,
} from "@/features/career/constants";
import { useCareerDashboard, useCareerWeeklyReview, useUpdateCareerProfile } from "@/features/career/use-career";

export function CareerDashboard() {
  const dashboardQuery = useCareerDashboard();
  const weeklyReviewQuery = useCareerWeeklyReview();
  const updateProfile = useUpdateCareerProfile();
  const [coachOpen, setCoachOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [headline, setHeadline] = useState("");
  const [summary, setSummary] = useState("");

  if (dashboardQuery.isLoading) return <LoadingState count={4} itemClassName="h-28" />;
  if (dashboardQuery.isError || !dashboardQuery.data) {
    return (
      <ErrorState
        message="We couldn't reach the API to load your career dashboard."
        retry={() => void dashboardQuery.refetch()}
      />
    );
  }

  const dashboard = dashboardQuery.data;

  function startEditingProfile() {
    setHeadline(dashboard.profile.headline ?? "");
    setSummary(dashboard.profile.summary ?? "");
    setEditingProfile(true);
  }

  function saveProfile() {
    updateProfile.mutate({ headline, summary }, { onSuccess: () => setEditingProfile(false) });
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between gap-3">
            <CardTitle>Career Profile</CardTitle>
            {!editingProfile ? (
              <Button size="sm" variant="outline" onClick={startEditingProfile}>
                Edit
              </Button>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {editingProfile ? (
            <>
              <Input
                value={headline}
                onChange={(event) => setHeadline(event.target.value)}
                placeholder="Headline (e.g. Aspiring Data Analyst)"
                aria-label="Headline"
              />
              <Textarea
                value={summary}
                onChange={(event) => setSummary(event.target.value)}
                placeholder="A short summary of where you are and what you're targeting"
                rows={3}
                aria-label="Summary"
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={saveProfile} disabled={updateProfile.isPending}>
                  Save
                </Button>
                <Button size="sm" variant="outline" onClick={() => setEditingProfile(false)}>
                  Cancel
                </Button>
              </div>
            </>
          ) : (
            <>
              <p className="font-medium text-foreground">{dashboard.profile.headline || "No headline yet"}</p>
              <p className="text-sm text-muted-foreground">
                {dashboard.profile.summary || "Add a summary to describe your target role and story."}
              </p>
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <Target className="size-4 text-primary" aria-hidden="true" />
              Primary Target Role
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard.primary_target_role ? (
              <>
                <p className="font-medium text-foreground">
                  {dashboard.primary_target_role.custom_title ?? dashboard.primary_target_role.role_template?.title ?? "Untitled role"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {dashboard.target_role_count} target role{dashboard.target_role_count === 1 ? "" : "s"} tracked
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No primary target role set.</p>
            )}
            <Button size="sm" variant="outline" className="mt-2" asChild>
              <Link href="/career/target-roles">Manage roles</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <TrendingUp className="size-4 text-primary" aria-hidden="true" />
              Latest Readiness
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboard.latest_assessment ? (
              <>
                <p className="text-2xl font-semibold text-foreground">
                  {dashboard.latest_assessment.overall_score.toFixed(0)}%
                </p>
                <Badge variant="outline">
                  {CAREER_READINESS_LEVEL_LABELS[dashboard.latest_assessment.overall_readiness_level]}
                </Badge>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No assessment computed yet.</p>
            )}
            <p className="mt-2 text-[11px] text-muted-foreground">{READINESS_DISCLAIMER}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <Trophy className="size-4 text-primary" aria-hidden="true" />
              Achievements
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold text-foreground">{dashboard.achievement_count}</p>
            <p className="text-xs text-muted-foreground">
              {dashboard.active_goal_count} active goal{dashboard.active_goal_count === 1 ? "" : "s"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5">
              <Briefcase className="size-4 text-primary" aria-hidden="true" />
              Saved Jobs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold text-foreground">{dashboard.saved_job_count}</p>
            <Button size="sm" variant="outline" className="mt-2" asChild>
              <Link href="/career/job-descriptions">View job descriptions</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Weekly Review</CardTitle>
        </CardHeader>
        <CardContent>
          {weeklyReviewQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-16" />
          ) : weeklyReviewQuery.isError ? (
            <ErrorState
              title="Unable to load your weekly review"
              message="We couldn't reach the API to load this week's activity."
              retry={() => void weeklyReviewQuery.refetch()}
            />
          ) : weeklyReviewQuery.data ? (
            <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-5">
              <div>
                <p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.exercises_passed}</p>
                <p className="text-xs text-muted-foreground">Exercises passed</p>
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.cases_completed}</p>
                <p className="text-xs text-muted-foreground">Cases completed</p>
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.projects_completed}</p>
                <p className="text-xs text-muted-foreground">Projects completed</p>
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.interviews_completed}</p>
                <p className="text-xs text-muted-foreground">Interviews completed</p>
              </div>
              <div>
                <p className="text-lg font-semibold text-foreground">{weeklyReviewQuery.data.new_milestones.length}</p>
                <p className="text-xs text-muted-foreground">New milestones</p>
              </div>
            </div>
          ) : null}
          <Button size="sm" variant="outline" className="mt-3" asChild>
            <Link href="/career/analytics">Full Career Analytics</Link>
          </Button>
        </CardContent>
      </Card>

      {dashboard.recent_milestones.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Recent Milestones</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-col gap-2">
              {dashboard.recent_milestones.map((milestone) => (
                <li key={milestone.id} className="flex items-center justify-between gap-2 text-sm">
                  <span className="text-foreground">{milestone.title}</span>
                  <Badge variant="outline">{CAREER_MILESTONE_TYPE_LABELS[milestone.milestone_type]}</Badge>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Quick Links</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Button variant="outline" asChild>
              <Link href="/career/target-roles">
                <Target className="size-4" aria-hidden="true" />
                Target Roles
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/career/job-descriptions">
                <FileText className="size-4" aria-hidden="true" />
                Job Descriptions
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/career/skill-gaps">
                <Puzzle className="size-4" aria-hidden="true" />
                Skill Gaps
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/career/resume">
                <FileBadge className="size-4" aria-hidden="true" />
                Resume
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/career/portfolio">
                <LayoutGrid className="size-4" aria-hidden="true" />
                Portfolio
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/career/interview-prep">
                <Mic className="size-4" aria-hidden="true" />
                Interview Prep
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/career/behavioral-stories">
                <Compass className="size-4" aria-hidden="true" />
                Behavioral Stories
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/career/analytics">
                <TrendingUp className="size-4" aria-hidden="true" />
                Career Analytics
              </Link>
            </Button>
          </div>
          <Button className="mt-4 gap-2" onClick={() => setCoachOpen(true)}>
            <Sparkles className="size-4" aria-hidden="true" />
            Ask the AI Career Coach
          </Button>
        </CardContent>
      </Card>

      <CareerCoachPanel open={coachOpen} onOpenChange={setCoachOpen} />
    </div>
  );
}
