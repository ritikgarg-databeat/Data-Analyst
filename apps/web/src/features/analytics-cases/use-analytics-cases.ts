import { useQuery } from "@tanstack/react-query";
import type { AnalyticsCase } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** The Case Library list (spec sections 33 & 44) — richer case-framing fields
 * than the plain exercise list. Submitting an attempt reuses the standard
 * exercise content/attempt hooks (`useExerciseContent`/`useSubmitExerciseAttempt`)
 * directly, since a case *is* an Exercise under the hood. */
export function useAnalyticsCases(domain?: string) {
  return useQuery({
    queryKey: ["analytics-cases", domain ?? null],
    queryFn: () =>
      apiClient.get<AnalyticsCase[]>(`/analytics/cases${domain ? `?domain=${encodeURIComponent(domain)}` : ""}`),
    staleTime: 30 * 1000,
  });
}
