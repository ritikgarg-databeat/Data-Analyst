import { useQuery } from "@tanstack/react-query";
import type { Exercise } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const exercisesQueryKey = ["exercises"] as const;

/** Fetches the full exercise list (no per-exercise prompt/content) for the /practice browser. */
export function useExercises() {
  return useQuery({
    queryKey: exercisesQueryKey,
    queryFn: () => apiClient.get<Exercise[]>("/exercises"),
    staleTime: 60 * 1000,
    retry: 1,
  });
}
