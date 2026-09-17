"use client";

import { ArrowDown, ArrowUp } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Exercise, UpdateExerciseAdminRequest } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exercisesQueryKey, useExercises } from "@/features/exercises/use-exercises";
import { apiClient } from "@/lib/api-client";

export function ExerciseAdminPanel() {
  const { data: exercises, isLoading, isError, refetch } = useExercises();
  const queryClient = useQueryClient();

  const updateExercise = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateExerciseAdminRequest }) =>
      apiClient.patch<Exercise>(`/exercises/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: exercisesQueryKey }),
  });

  if (isLoading) return <LoadingState count={4} itemClassName="h-12" />;
  if (isError) {
    return (
      <ErrorState title="Unable to load exercises" message="We couldn't reach the API." retry={() => void refetch()} />
    );
  }

  const sorted = [...(exercises ?? [])].sort((a, b) => a.display_order - b.display_order);

  function swapOrder(a: Exercise, b: Exercise) {
    updateExercise.mutate({ id: a.id, body: { display_order: b.display_order } });
    updateExercise.mutate({ id: b.id, body: { display_order: a.display_order } });
  }

  return (
    <div className="space-y-4">
      <p className="rounded-lg border border-border bg-muted/30 px-4 py-2 text-xs text-muted-foreground">
        Exercise content is authored in <code>content/exercises/</code> files — edit those and run{" "}
        <code>sync-content</code> to change the prompt, hints, or solution. Here you can only reorder or
        activate/deactivate.
      </p>

      <div className="divide-y divide-border rounded-lg border border-border">
        {sorted.map((exercise, index) => (
          <div key={exercise.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                {exercise.title} <span className="text-xs text-muted-foreground">({exercise.slug})</span>
              </p>
              <p className="text-xs text-muted-foreground">
                {exercise.exercise_type.replace(/_/g, " ")} · {exercise.points} pts
              </p>
            </div>
            <div className="flex items-center gap-1">
              <Button
                size="icon"
                variant="ghost"
                aria-label="Move up"
                disabled={index === 0}
                onClick={() => swapOrder(exercise, sorted[index - 1])}
              >
                <ArrowUp className="size-4" aria-hidden="true" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                aria-label="Move down"
                disabled={index === sorted.length - 1}
                onClick={() => swapOrder(exercise, sorted[index + 1])}
              >
                <ArrowDown className="size-4" aria-hidden="true" />
              </Button>
              <Badge variant={exercise.is_active ? "success" : "outline"}>
                {exercise.is_active ? "Active" : "Inactive"}
              </Badge>
              <Button
                size="sm"
                variant="ghost"
                onClick={() =>
                  updateExercise.mutate({ id: exercise.id, body: { is_active: !exercise.is_active } })
                }
              >
                {exercise.is_active ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
