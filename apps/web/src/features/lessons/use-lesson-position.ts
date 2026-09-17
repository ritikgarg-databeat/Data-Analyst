import { useMutation } from "@tanstack/react-query";
import type { LessonProgress, UpdateLessonPositionRequest } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Records the reader's scroll position + elapsed time for a lesson. Used for
 * periodic "still reading" pings and a final flush on unmount, so a reload
 * can resume near where the learner left off.
 */
export function useUpdateLessonPosition(slug: string) {
  return useMutation({
    mutationFn: (body: UpdateLessonPositionRequest) =>
      apiClient.post<LessonProgress>(`/lessons/${slug}/position`, body),
  });
}
