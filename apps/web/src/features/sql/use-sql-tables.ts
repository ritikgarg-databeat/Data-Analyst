import { useQuery } from "@tanstack/react-query";
import type { SqlTableSummary } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function sqlTablesQueryKey(database: string, engine: string) {
  return ["sql", "databases", database, "tables", engine] as const;
}

/** Lists the tables in one database (grain, row count, column count). */
export function useSqlTables(database: string, engine: string) {
  return useQuery({
    queryKey: sqlTablesQueryKey(database, engine),
    queryFn: () =>
      apiClient.get<SqlTableSummary[]>(
        `/sql/databases/${encodeURIComponent(database)}/tables?engine=${encodeURIComponent(engine)}`,
      ),
    staleTime: 60 * 1000,
    enabled: Boolean(database) && Boolean(engine),
  });
}
