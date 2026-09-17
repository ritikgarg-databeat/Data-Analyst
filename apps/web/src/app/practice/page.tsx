"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Dumbbell } from "lucide-react";
import type { DifficultyLevel, ExerciseType } from "@data-analyst-lab/shared";

import { DifficultyBadge } from "@/components/features/curriculum/difficulty-badge";
import { FilterGroup } from "@/components/features/curriculum/filter-group";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useExercises } from "@/features/exercises/use-exercises";

type DifficultyFilter = DifficultyLevel | "ALL";
type TypeFilter = ExerciseType | "ALL";

const DIFFICULTY_OPTIONS: { value: DifficultyFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "BEGINNER", label: "Beginner" },
  { value: "INTERMEDIATE", label: "Intermediate" },
  { value: "ADVANCED", label: "Advanced" },
];

export default function PracticePage() {
  const { data: exercises, isLoading, isError, refetch } = useExercises();
  const [difficultyFilter, setDifficultyFilter] = useState<DifficultyFilter>("ALL");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("ALL");

  const typeOptions = useMemo<{ value: TypeFilter; label: string }[]>(() => {
    const types = Array.from(new Set((exercises ?? []).map((e) => e.exercise_type)));
    return [{ value: "ALL", label: "All" }, ...types.map((t) => ({ value: t, label: t.replace(/_/g, " ") }))];
  }, [exercises]);

  const filtered = (exercises ?? []).filter((exercise) => {
    if (difficultyFilter !== "ALL" && exercise.difficulty !== difficultyFilter) return false;
    if (typeFilter !== "ALL" && exercise.exercise_type !== typeFilter) return false;
    return true;
  });

  return (
    <div>
      <PageHeader title="Practice" subtitle="Standalone exercises across every domain, with instant feedback." />

      {isLoading ? (
        <LoadingState count={6} className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" itemClassName="h-32" />
      ) : isError ? (
        <ErrorState
          title="Unable to load exercises"
          message="We couldn't reach the API to load the exercise list."
          retry={() => void refetch()}
        />
      ) : !exercises || exercises.length === 0 ? (
        <EmptyState
          icon={Dumbbell}
          title="No exercises yet"
          description="Exercises will appear here once they're added to the curriculum."
        />
      ) : (
        <>
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-6">
            <FilterGroup
              label="Difficulty"
              options={DIFFICULTY_OPTIONS}
              value={difficultyFilter}
              onChange={setDifficultyFilter}
            />
            <FilterGroup label="Type" options={typeOptions} value={typeFilter} onChange={setTypeFilter} />
          </div>

          {filtered.length === 0 ? (
            <EmptyState
              icon={Dumbbell}
              title="No exercises match"
              description="Try a different difficulty or type filter."
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((exercise) => (
                <Link
                  key={exercise.id}
                  href={`/practice/${exercise.slug}`}
                  className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                >
                  <Card className="h-full transition-shadow hover:shadow-md">
                    <CardHeader>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="outline">{exercise.exercise_type.replace(/_/g, " ")}</Badge>
                        <DifficultyBadge difficulty={exercise.difficulty} />
                      </div>
                      <CardTitle className="text-base">{exercise.title}</CardTitle>
                    </CardHeader>
                    <CardContent className="flex items-center justify-between text-xs text-muted-foreground">
                      <span>{exercise.skill_slug ?? "General"}</span>
                      <span>{exercise.points} pts</span>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
