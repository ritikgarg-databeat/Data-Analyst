import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { SubmitSqlExerciseRequest, SubmitSqlExerciseResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";
import { exerciseContentQueryKey } from "@/features/exercises/use-exercise-content";

/** Submits a query for grading against a SQL exercise's (hidden) test suite. */
export function useSubmitSqlExercise(slug: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: SubmitSqlExerciseRequest) =>
      apiClient.post<SubmitSqlExerciseResponse>(`/sql/exercises/${slug}/submit`, body),
    onSuccess: () => {
      // attempt_count / best_attempt on the generic exercise content payload are now stale.
      void queryClient.invalidateQueries({ queryKey: exerciseContentQueryKey(slug) });
    },
  });
}
