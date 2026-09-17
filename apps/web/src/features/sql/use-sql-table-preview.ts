import { useQuery } from "@tanstack/react-query";
import type { SqlTablePreview } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function sqlTablePreviewQueryKey(database: string, table: string, engine: string) {
  return ["sql", "databases", database, "tables", table, "preview", engine] as const;
}

interface UseSqlTablePreviewOptions {
  /** Defer the fetch until the caller wants it (e.g. a preview panel is opened). Defaults to true. */
  enabled?: boolean;
}

/** Fetches a small sample of a table's rows, plus per-column null counts. */
export function useSqlTablePreview(
  database: string,
  table: string,
  engine: string,
  options: UseSqlTablePreviewOptions = {},
) {
  return useQuery({
    queryKey: sqlTablePreviewQueryKey(database, table, engine),
    queryFn: () =>
      apiClient.get<SqlTablePreview>(
        `/sql/databases/${encodeURIComponent(database)}/tables/${encodeURIComponent(table)}/preview?engine=${encodeURIComponent(engine)}`,
      ),
    staleTime: 5 * 60 * 1000,
    enabled: (options.enabled ?? true) && Boolean(database) && Boolean(table) && Boolean(engine),
  });
}
