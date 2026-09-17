import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  Chart,
  ChartDataResponse,
  CreateChartRequest,
  RecommendRequest,
  RecommendResponse,
  UpdateChartRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

function chartsKey(datasetId?: string) {
  return ["charts", datasetId ?? "all"] as const;
}

export function useCharts(datasetId?: string) {
  return useQuery({
    queryKey: chartsKey(datasetId),
    queryFn: () => apiClient.get<Chart[]>(`/charts${datasetId ? `?dataset_id=${datasetId}` : ""}`),
    staleTime: 15 * 1000,
  });
}

export function useChart(id: string | undefined) {
  return useQuery({
    queryKey: ["charts", "detail", id],
    queryFn: () => apiClient.get<Chart>(`/charts/${id}`),
    enabled: Boolean(id),
  });
}

export function useChartData(id: string | undefined) {
  return useQuery({
    queryKey: ["charts", "detail", id, "data"],
    queryFn: () => apiClient.get<ChartDataResponse>(`/charts/${id}/data`),
    enabled: Boolean(id),
    staleTime: 15 * 1000,
  });
}

export function useCreateChart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateChartRequest) => apiClient.post<Chart>("/charts", payload),
    onSuccess: (chart) => {
      void queryClient.invalidateQueries({ queryKey: chartsKey(chart.dataset_id) });
      void queryClient.invalidateQueries({ queryKey: chartsKey() });
    },
  });
}

export function useUpdateChart(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateChartRequest) => apiClient.patch<Chart>(`/charts/${id}`, payload),
    onSuccess: (chart) => {
      queryClient.setQueryData(["charts", "detail", id], chart);
      void queryClient.invalidateQueries({ queryKey: ["charts", "detail", id, "data"] });
      void queryClient.invalidateQueries({ queryKey: chartsKey(chart.dataset_id) });
    },
  });
}

export function useDeleteChart() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/charts/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["charts"] });
    },
  });
}

/** Deterministic chart-type recommendation from a pair of variable types (no chart needs to exist yet). */
export function useRecommendChart() {
  return useMutation({
    mutationFn: (payload: RecommendRequest) => apiClient.post<RecommendResponse>("/charts/recommend", payload),
  });
}
