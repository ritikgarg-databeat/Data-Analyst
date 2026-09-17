import { useQuery } from "@tanstack/react-query";
import type { SqlEngineInfo } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function sqlEnginesQueryKey() {
  return ["sql", "engines"] as const;
}

/** Lists SQL execution engines (e.g. duckdb, postgres) and whether each is currently usable. */
export function useSqlEngines() {
  return useQuery({
    queryKey: sqlEnginesQueryKey(),
    queryFn: () => apiClient.get<SqlEngineInfo[]>("/sql/engines"),
    staleTime: 5 * 60 * 1000,
  });
}
