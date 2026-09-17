import { useQuery } from "@tanstack/react-query";
import type { LessonContentResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function lessonContentQueryKey(slug: string) {
  return ["lessons", slug, "content"] as const;
}

/** Fetches the full lesson reader payload (blocks, progress, lock state, nav). */
export function useLessonContent(slug: string) {
  return useQuery({
    queryKey: lessonContentQueryKey(slug),
    queryFn: () => apiClient.get<LessonContentResponse>(`/lessons/${slug}/content`),
    staleTime: 60 * 1000,
    retry: 1,
    enabled: Boolean(slug),
  });
}
