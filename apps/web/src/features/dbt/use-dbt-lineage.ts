import { useQuery } from "@tanstack/react-query";
import type { LineageGraphSchema } from "@data-analyst-lab/shared";

import { ApiError, apiClient } from "@/lib/api-client";

/** The real project DAG, built from dbt's own manifest.json — 400s until at least one dbt command has run. */
export function useDbtLineage() {
  return useQuery({
    queryKey: ["dbt", "lineage"] as const,
    queryFn: () => apiClient.get<LineageGraphSchema>("/dbt/lineage"),
    staleTime: 5 * 1000,
    retry: (failureCount, error) => error instanceof ApiError && error.status >= 500 && failureCount < 2,
  });
}
