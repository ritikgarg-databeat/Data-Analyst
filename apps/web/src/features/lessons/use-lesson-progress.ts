import { useMutation } from "@tanstack/react-query";
import type { LessonProgress, UpsertLessonProgressRequest } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Upserts lesson progress status/percent. The server enforces completion
 * rules itself (e.g. won't mark COMPLETED below the reading threshold) — the
 * caller must always render whatever `status` comes back, not assume success.
 */
export function useUpsertLessonProgress(lessonId: string) {
  return useMutation({
    mutationFn: (body: UpsertLessonProgressRequest) =>
      apiClient.post<LessonProgress>(`/progress/lessons/${lessonId}`, body),
  });
}
