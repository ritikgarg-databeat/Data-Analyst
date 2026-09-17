"use client";

import { useMemo, useState } from "react";
import { Puzzle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { SKILL_CATEGORY_LABELS } from "@data-analyst-lab/shared";
import { CAREER_SKILL_EVIDENCE_LEVEL_LABELS } from "@/features/career/constants";
import { useCareerSkillMatrix } from "@/features/career/use-career";
import { cn } from "@/lib/utils";

export function SkillGapsPage() {
  const skillMatrixQuery = useCareerSkillMatrix();
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const entries = skillMatrixQuery.data ?? [];
    const term = search.trim().toLowerCase();
    if (!term) return entries;
    return entries.filter(
      (entry) => entry.name.toLowerCase().includes(term) || entry.skill_slug.toLowerCase().includes(term),
    );
  }, [skillMatrixQuery.data, search]);

  const gapCount = (skillMatrixQuery.data ?? []).filter((entry) => entry.is_gap_for_primary_role).length;

  if (skillMatrixQuery.isLoading) return <LoadingState count={4} itemClassName="h-10" />;
  if (skillMatrixQuery.isError) {
    return (
      <ErrorState
        message="We couldn't reach the API to load your career skill matrix."
        retry={() => void skillMatrixQuery.refetch()}
      />
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>
              Career Skill Matrix
              {gapCount > 0 ? (
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  {gapCount} skill{gapCount === 1 ? "" : "s"} flagged as a gap for your primary role
                </span>
              ) : null}
            </CardTitle>
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search skills..."
              className="w-56"
              aria-label="Search skills"
            />
          </div>
        </CardHeader>
        <CardContent>
          {filtered.length === 0 ? (
            <EmptyState icon={Puzzle} title="No skills found" description="Try clearing the search box above." />
          ) : (
            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full min-w-max border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
                    <th className="px-4 py-2.5">Skill</th>
                    <th className="px-4 py-2.5">Category</th>
                    <th className="px-4 py-2.5">Mastery</th>
                    <th className="px-4 py-2.5">Evidence</th>
                    <th className="px-4 py-2.5">Exercises</th>
                    <th className="px-4 py-2.5">Projects</th>
                    <th className="px-4 py-2.5">Cases</th>
                    <th className="px-4 py-2.5">Mock Interview</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((entry) => (
                    <tr
                      key={entry.skill_slug}
                      className={cn(
                        "border-b border-border last:border-0",
                        entry.is_gap_for_primary_role && "bg-destructive/5",
                      )}
                    >
                      <td className="px-4 py-2 text-foreground">
                        <div className="flex items-center gap-1.5">
                          {entry.name}
                          {entry.is_gap_for_primary_role ? <Badge variant="destructive">Gap</Badge> : null}
                        </div>
                      </td>
                      <td className="px-4 py-2 text-muted-foreground">{SKILL_CATEGORY_LABELS[entry.category]}</td>
                      <td className="px-4 py-2 text-foreground">{entry.mastery_score.toFixed(0)}%</td>
                      <td className="px-4 py-2">
                        <Badge variant="outline">{CAREER_SKILL_EVIDENCE_LEVEL_LABELS[entry.evidence_level]}</Badge>
                      </td>
                      <td className="px-4 py-2 text-muted-foreground">{entry.exercises_passed}</td>
                      <td className="px-4 py-2 text-muted-foreground">{entry.projects_count}</td>
                      <td className="px-4 py-2 text-muted-foreground">{entry.cases_count}</td>
                      <td className="px-4 py-2 text-muted-foreground">
                        {entry.mock_interview_score != null ? `${entry.mock_interview_score.toFixed(0)}%` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
