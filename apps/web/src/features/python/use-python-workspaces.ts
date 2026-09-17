import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  CreatePythonWorkspaceRequest,
  PythonWorkspaceSchema,
  UpdatePythonWorkspaceRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function pythonWorkspacesQueryKey() {
  return ["python", "workspaces"] as const;
}

export function pythonWorkspaceQueryKey(workspaceId: string) {
  return ["python", "workspaces", workspaceId] as const;
}

/** Lists this user's Python Lab workspaces (each a named notebook of cells). */
export function usePythonWorkspaces() {
  return useQuery({
    queryKey: pythonWorkspacesQueryKey(),
    queryFn: () => apiClient.get<PythonWorkspaceSchema[]>("/python/workspaces"),
    staleTime: 60 * 1000,
  });
}

/** Fetches one workspace. */
export function usePythonWorkspace(workspaceId: string | null) {
  return useQuery({
    queryKey: pythonWorkspaceQueryKey(workspaceId ?? ""),
    queryFn: () => apiClient.get<PythonWorkspaceSchema>(`/python/workspaces/${workspaceId}`),
    enabled: Boolean(workspaceId),
    staleTime: 60 * 1000,
  });
}

/** Creates a new workspace. Creating one auto-creates a single empty starter cell server-side. */
export function useCreatePythonWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: CreatePythonWorkspaceRequest) =>
      apiClient.post<PythonWorkspaceSchema>("/python/workspaces", body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pythonWorkspacesQueryKey() });
    },
  });
}

/** Renames/edits a workspace. */
export function useUpdatePythonWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdatePythonWorkspaceRequest }) =>
      apiClient.patch<PythonWorkspaceSchema>(`/python/workspaces/${id}`, body),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: pythonWorkspacesQueryKey() });
      void queryClient.invalidateQueries({ queryKey: pythonWorkspaceQueryKey(variables.id) });
    },
  });
}

/** Deletes a workspace and all its cells. */
export function useDeletePythonWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/python/workspaces/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pythonWorkspacesQueryKey() });
    },
  });
}
