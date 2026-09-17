import { useQuery } from "@tanstack/react-query";
import type { DuplicatesResponse, OutliersResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Sample of fully duplicate rows for one table (lazily fetched — pass `enabled` to gate it behind an "Inspect" click). */
export function useDatasetDuplicates(idOrSlug: string | undefined, table: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "duplicates", table],
    queryFn: () =>
      apiClient.get<DuplicatesResponse>(
        `/datasets/${encodeURIComponent(idOrSlug!)}/duplicates${table ? `?table=${encodeURIComponent(table)}` : ""}`,
      ),
    enabled: Boolean(idOrSlug) && enabled,
    staleTime: 30 * 1000,
  });
}

/** Sample of statistical outlier rows for one numeric column. */
export function useDatasetOutliers(
  idOrSlug: string | undefined,
  table: string | undefined,
  column: string | undefined,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "outliers", table, column],
    queryFn: () => {
      const params = new URLSearchParams({ column: column! });
      if (table) params.set("table", table);
      return apiClient.get<OutliersResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/outliers?${params}`);
    },
    enabled: Boolean(idOrSlug) && Boolean(column) && enabled,
    staleTime: 30 * 1000,
  });
}
