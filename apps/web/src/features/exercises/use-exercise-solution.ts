import { useMutation } from "@tanstack/react-query";
import type { RevealSolutionResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Reveals the worked solution + explanation for an exercise. */
export function useRevealExerciseSolution(slug: string) {
  return useMutation({
    mutationFn: () => apiClient.post<RevealSolutionResponse>(`/exercises/${slug}/solution`),
  });
}
