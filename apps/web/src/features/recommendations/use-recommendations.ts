import { useQuery } from "@tanstack/react-query";
import type { RecommendationItem } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function recommendationsQueryKey(limit: number) {
  return ["recommendations", limit] as const;
}

/** Deterministic "what to study next" — server-prioritized, just render in order. */
export function useRecommendations(limit = 5) {
  return useQuery({
    queryKey: recommendationsQueryKey(limit),
    queryFn: () => apiClient.get<RecommendationItem[]>(`/recommendations?limit=${limit}`),
    staleTime: 30 * 1000,
    retry: 1,
  });
}
