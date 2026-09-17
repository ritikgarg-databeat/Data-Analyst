import { useQuery } from "@tanstack/react-query";
import type { TableSchemaResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Fetches the schema (column name/type/null%/unique%) for every table in a dataset, or just one. */
export function useDatasetSchema(idOrSlug: string | undefined, table?: string) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "schema", table ?? "*"],
    queryFn: () =>
      apiClient.get<TableSchemaResponse[]>(
        `/datasets/${encodeURIComponent(idOrSlug!)}/schema${table ? `?table=${encodeURIComponent(table)}` : ""}`,
      ),
    enabled: Boolean(idOrSlug),
    staleTime: 30 * 1000,
  });
}
