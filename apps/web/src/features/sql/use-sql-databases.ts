import { useQuery } from "@tanstack/react-query";
import type { SqlDatabaseInfo } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function sqlDatabasesQueryKey() {
  return ["sql", "databases"] as const;
}

/** Lists the databases available for SQL Lab (each backed by one engine). */
export function useSqlDatabases() {
  return useQuery({
    queryKey: sqlDatabasesQueryKey(),
    queryFn: () => apiClient.get<SqlDatabaseInfo[]>("/sql/databases"),
    staleTime: 5 * 60 * 1000,
  });
}
