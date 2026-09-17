import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  CreateSqlSavedQueryRequest,
  SqlSavedQuerySchema,
  UpdateSqlSavedQueryRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Stable prefix shared by every saved-queries query key — pass to invalidateQueries to bust all workspace filters at once. */
export function sqlSavedQueriesQueryKeyPrefix() {
  return ["sql", "saved"] as const;
}

export function sqlSavedQueriesQueryKey(workspaceId?: string) {
  return [...sqlSavedQueriesQueryKeyPrefix(), workspaceId ?? null] as const;
}

/** Lists saved queries, optionally scoped to one workspace. */
export function useSqlSavedQueries(workspaceId?: string) {
  return useQuery({
    queryKey: sqlSavedQueriesQueryKey(workspaceId),
    queryFn: () =>
      apiClient.get<SqlSavedQuerySchema[]>(
        `/sql/saved${workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ""}`,
      ),
    staleTime: 30 * 1000,
  });
}

/** Saves the current query under a title (+ optional description/tags). */
export function useCreateSqlSavedQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CreateSqlSavedQueryRequest) => apiClient.post<SqlSavedQuerySchema>("/sql/saved", body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sqlSavedQueriesQueryKeyPrefix() });
    },
  });
}

/** Renames/edits a saved query. */
export function useUpdateSqlSavedQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateSqlSavedQueryRequest }) =>
      apiClient.patch<SqlSavedQuerySchema>(`/sql/saved/${id}`, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sqlSavedQueriesQueryKeyPrefix() });
    },
  });
}

/** Deletes a saved query. */
export function useDeleteSqlSavedQuery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/sql/saved/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sqlSavedQueriesQueryKeyPrefix() });
    },
  });
}
