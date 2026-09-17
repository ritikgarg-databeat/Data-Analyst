import { useQuery } from "@tanstack/react-query";
import type { MetricDefinition } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function useMetrics(params?: { category?: string; q?: string }) {
  const search = new URLSearchParams();
  if (params?.category) search.set("category", params.category);
  if (params?.q) search.set("q", params.q);
  const qs = search.toString();
  return useQuery({
    queryKey: ["metrics", params?.category ?? null, params?.q ?? null],
    queryFn: () => apiClient.get<MetricDefinition[]>(`/metrics${qs ? `?${qs}` : ""}`),
    staleTime: 60 * 1000,
  });
}

export function useMetric(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: ["metrics", idOrSlug],
    queryFn: () => apiClient.get<MetricDefinition>(`/metrics/${encodeURIComponent(idOrSlug!)}`),
    enabled: Boolean(idOrSlug),
    staleTime: 60 * 1000,
  });
}
