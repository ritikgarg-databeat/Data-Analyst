import { useQuery } from "@tanstack/react-query";
import type { Lesson } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const moduleLessonsQueryKey = (slug: string) => ["modules", slug, "lessons"] as const;

/** Fetches every lesson in a module, used by the module page's lesson list. */
export function useModuleLessons(slug: string) {
  return useQuery({
    queryKey: moduleLessonsQueryKey(slug),
    queryFn: () => apiClient.get<Lesson[]>(`/modules/${slug}/lessons`),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: Boolean(slug),
  });
}
