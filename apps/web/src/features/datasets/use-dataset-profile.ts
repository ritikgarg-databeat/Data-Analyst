import { useQuery } from "@tanstack/react-query";
import type { DatasetProfileResponse, DatasetQualityResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Full column-level profile (types, nulls, stats, top values, outliers) for every table in a dataset. */
export function useDatasetProfile(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "profile"],
    queryFn: () => apiClient.get<DatasetProfileResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/profile`),
    enabled: Boolean(idOrSlug),
    staleTime: 30 * 1000,
  });
}

/** The deterministic data-quality report (completeness/uniqueness/validity/consistency) for every table. */
export function useDatasetQuality(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "quality"],
    queryFn: () => apiClient.get<DatasetQualityResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/quality`),
    enabled: Boolean(idOrSlug),
    staleTime: 30 * 1000,
  });
}
