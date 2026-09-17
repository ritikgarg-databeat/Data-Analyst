import { useQuery } from "@tanstack/react-query";
import type { DatasetUsageSchema, DatasetVersionSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function useDatasetVersions(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "versions"],
    queryFn: () => apiClient.get<DatasetVersionSchema[]>(`/datasets/${encodeURIComponent(idOrSlug!)}/versions`),
    enabled: Boolean(idOrSlug),
    staleTime: 30 * 1000,
  });
}

export function useDatasetUsage(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "usage"],
    queryFn: () => apiClient.get<DatasetUsageSchema>(`/datasets/${encodeURIComponent(idOrSlug!)}/usage`),
    enabled: Boolean(idOrSlug),
    staleTime: 30 * 1000,
  });
}
