import { useQuery } from "@tanstack/react-query";
import type { LessonProgress } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const lessonProgressQueryKey = ["progress", "lessons"] as const;

/** Fetches the current user's per-lesson progress, joined client-side with lesson lists. */
export function useLessonProgress() {
  return useQuery({
    queryKey: lessonProgressQueryKey,
    queryFn: () => apiClient.get<LessonProgress[]>("/progress/lessons"),
    staleTime: 60 * 1000,
    retry: 1,
  });
}
