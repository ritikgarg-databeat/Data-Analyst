import { useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  SubmitExerciseAttemptRequest,
  SubmitExerciseAttemptResponse,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

import { exerciseContentQueryKey } from "./use-exercise-content";

/** Submits an attempt for one exercise; auto-graded types come back scored immediately. */
export function useSubmitExerciseAttempt(slug: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: SubmitExerciseAttemptRequest) =>
      apiClient.post<SubmitExerciseAttemptResponse>(`/exercises/${slug}/attempts`, body),
    onSuccess: () => {
      // attempt_count / best_attempt on the content payload are now stale.
      void queryClient.invalidateQueries({ queryKey: exerciseContentQueryKey(slug) });
    },
  });
}
