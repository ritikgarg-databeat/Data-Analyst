import { useMutation } from "@tanstack/react-query";
import type { RevealHintResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Reveals the next progressive hint for an exercise (one call per reveal). */
export function useRevealExerciseHint(slug: string) {
  return useMutation({
    mutationFn: () => apiClient.post<RevealHintResponse>(`/exercises/${slug}/hint`),
  });
}
