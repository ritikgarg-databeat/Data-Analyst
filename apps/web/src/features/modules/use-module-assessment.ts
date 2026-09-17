import { useQuery } from "@tanstack/react-query";
import type { Assessment } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const moduleAssessmentQueryKey = (slug: string) => ["modules", slug, "assessment"] as const;

/** Fetches a module's assessment — only enabled when the module actually has one. */
export function useModuleAssessment(slug: string, enabled: boolean) {
  return useQuery({
    queryKey: moduleAssessmentQueryKey(slug),
    queryFn: () => apiClient.get<Assessment>(`/modules/${slug}/assessment`),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: Boolean(slug) && enabled,
  });
}
