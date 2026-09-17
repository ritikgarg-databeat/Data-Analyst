import { useQuery } from "@tanstack/react-query";
import type { ExerciseContent } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function exerciseContentQueryKey(slug: string) {
  return ["exercises", slug, "content"] as const;
}

/** Fetches one exercise's attemptable content (prompt/choices, never the answer). */
export function useExerciseContent(slug: string) {
  return useQuery({
    queryKey: exerciseContentQueryKey(slug),
    queryFn: () => apiClient.get<ExerciseContent>(`/exercises/${slug}/content`),
    staleTime: 30 * 1000,
    retry: 1,
    enabled: Boolean(slug),
  });
}
