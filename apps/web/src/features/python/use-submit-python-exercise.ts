import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { SubmitPythonExerciseRequest, SubmitPythonExerciseResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";
import { exerciseContentQueryKey } from "@/features/exercises/use-exercise-content";

/** Submits code for grading against a Python exercise's (hidden) test suite. */
export function useSubmitPythonExercise(slug: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: SubmitPythonExerciseRequest) =>
      apiClient.post<SubmitPythonExerciseResponse>(`/python/exercises/${slug}/submit`, body),
    onSuccess: () => {
      // attempt_count / best_attempt on the generic exercise content payload are now stale.
      void queryClient.invalidateQueries({ queryKey: exerciseContentQueryKey(slug) });
    },
  });
}
