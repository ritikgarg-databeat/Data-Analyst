import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateSqlWorkspaceRequest, SqlWorkspaceSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function sqlWorkspacesQueryKey() {
  return ["sql", "workspaces"] as const;
}

/** Lists this user's SQL Lab workspaces. */
export function useSqlWorkspaces() {
  return useQuery({
    queryKey: sqlWorkspacesQueryKey(),
    queryFn: () => apiClient.get<SqlWorkspaceSchema[]>("/sql/workspaces"),
    staleTime: 60 * 1000,
  });
}

/** Creates a new workspace (a named engine+database pairing to group saved queries under). */
export function useCreateSqlWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CreateSqlWorkspaceRequest) => apiClient.post<SqlWorkspaceSchema>("/sql/workspaces", body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: sqlWorkspacesQueryKey() });
    },
  });
}
