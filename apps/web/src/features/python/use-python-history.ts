import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { PythonHistoryItemSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export interface PythonHistoryFilters {
  workspaceId?: string;
  limit?: number;
}

/** Stable prefix shared by every history query key — pass to invalidateQueries to bust all filter variants at once. */
export function pythonHistoryQueryKeyPrefix() {
  return ["python", "history"] as const;
}

export function pythonHistoryQueryKey(filters: PythonHistoryFilters = {}) {
  return [...pythonHistoryQueryKeyPrefix(), filters] as const;
}

/** Lists this user's past Python Lab executions, most recent first. */
export function usePythonHistory(filters: PythonHistoryFilters = {}) {
  const params = new URLSearchParams();
  if (filters.workspaceId) params.set("workspace_id", filters.workspaceId);
  if (filters.limit != null) params.set("limit", String(filters.limit));
  const qs = params.toString();

  return useQuery({
    queryKey: pythonHistoryQueryKey(filters),
    queryFn: () => apiClient.get<PythonHistoryItemSchema[]>(`/python/history${qs ? `?${qs}` : ""}`),
    staleTime: 10 * 1000,
  });
}

/** Deletes one history entry. */
export function useDeletePythonHistoryEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/python/history/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pythonHistoryQueryKeyPrefix() });
    },
  });
}
