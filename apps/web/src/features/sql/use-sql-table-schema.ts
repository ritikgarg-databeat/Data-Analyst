import { useQuery } from "@tanstack/react-query";
import type { SqlTableSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function sqlTableSchemaQueryKey(database: string, table: string, engine: string) {
  return ["sql", "databases", database, "tables", table, "schema", engine] as const;
}

interface UseSqlTableSchemaOptions {
  /** Defer the fetch until the caller wants it (e.g. a tree node is expanded). Defaults to true. */
  enabled?: boolean;
}

/** Fetches one table's column list (name/type/nullable) and row count — used by the schema explorer's lazy expand. */
export function useSqlTableSchema(
  database: string,
  table: string,
  engine: string,
  options: UseSqlTableSchemaOptions = {},
) {
  return useQuery({
    queryKey: sqlTableSchemaQueryKey(database, table, engine),
    queryFn: () =>
      apiClient.get<SqlTableSchema>(
        `/sql/databases/${encodeURIComponent(database)}/tables/${encodeURIComponent(table)}/schema?engine=${encodeURIComponent(engine)}`,
      ),
    staleTime: 5 * 60 * 1000,
    enabled: (options.enabled ?? true) && Boolean(database) && Boolean(table) && Boolean(engine),
  });
}
