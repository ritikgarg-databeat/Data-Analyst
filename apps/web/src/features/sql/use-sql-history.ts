import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { SqlQueryHistoryItem } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export interface SqlHistoryFilters {
  limit?: number;
  status?: string;
  engine?: string;
}

/** Stable prefix shared by every history query key — pass to invalidateQueries to bust all filter variants at once. */
export function sqlHistoryQueryKeyPrefix() {
  return ["sql", "history"] as const;
}

export function sqlHistoryQueryKey(filters: SqlHistoryFilters = {}) {
  return [...sqlHistoryQueryKeyPrefix(), filters] as const;
}

/** Lists this user's past query executions, most recent first. */
export function useSqlHistory(filters: SqlHistoryFilters = {}) {
  const params = new URLSearchParams();
  if (filters.limit != null) params.set("limit", String(filters.limit));
  if (filters.status) params.set("status", filters.status);
  if (filters.engine) params.set("engine", filters.engine);
  const qs = params.toString();

  return useQuery({
    queryKey: sqlHistoryQueryKey(filters),
    queryFn: () => apiClient.get<SqlQueryHistoryItem[]>(`/sql/history${qs ? `?${qs}` : ""}`),
    staleTime: 10 * 1000,
  });
}

/** Deletes one history entry. */
export function useDeleteSqlHistoryEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/sql/history/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sqlHistoryQueryKeyPrefix() });
    },
  });
}
