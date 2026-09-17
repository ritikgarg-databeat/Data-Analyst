import { useQuery } from "@tanstack/react-query";
import type { TestResultSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Results from the most recent `dbt test`/`dbt build` — empty/400 if the last command wasn't one of those. */
export function useDbtTestResults() {
  return useQuery({
    queryKey: ["dbt", "test-results"] as const,
    queryFn: () => apiClient.get<TestResultSchema[]>("/dbt/test-results"),
    staleTime: 5 * 1000,
  });
}
