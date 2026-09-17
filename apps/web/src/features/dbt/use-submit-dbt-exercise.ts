import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { SubmitDbtExerciseRequest, SubmitDbtExerciseResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";
import { exerciseContentQueryKey } from "@/features/exercises/use-exercise-content";

/** Submits a dbt model's SQL for grading — writes it into the real dbt project and runs `dbt build --select`. */
export function useSubmitDbtExercise(slug: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: SubmitDbtExerciseRequest) =>
      apiClient.post<SubmitDbtExerciseResponse>(`/dbt/exercises/${slug}/submit`, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: exerciseContentQueryKey(slug) });
    },
  });
}
