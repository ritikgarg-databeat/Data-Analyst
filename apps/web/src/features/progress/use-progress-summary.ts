import { useQuery } from "@tanstack/react-query";
import type { ProgressSummary } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const progressSummaryQueryKey = ["progress", "summary"] as const;

/** Fetches the dashboard progress summary (overall %, streak, skill overview, continue learning). */
export function useProgressSummary() {
  return useQuery({
    queryKey: progressSummaryQueryKey,
    queryFn: () => apiClient.get<ProgressSummary>("/progress/summary"),
    staleTime: 60 * 1000,
    retry: 1,
  });
}
