import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { PythonRuntimeSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function pythonRuntimesQueryKey() {
  return ["python", "runtimes"] as const;
}

export function pythonRuntimeQueryKey(runtimeId: string) {
  return ["python", "runtimes", runtimeId] as const;
}

/** Lists this user's live Python runtimes (sandboxes). */
export function usePythonRuntimes() {
  return useQuery({
    queryKey: pythonRuntimesQueryKey(),
    queryFn: () => apiClient.get<PythonRuntimeSchema[]>("/python/runtimes"),
    staleTime: 10 * 1000,
  });
}

/** Fetches one runtime's current status. */
export function usePythonRuntime(runtimeId: string | null) {
  return useQuery({
    queryKey: pythonRuntimeQueryKey(runtimeId ?? ""),
    queryFn: () => apiClient.get<PythonRuntimeSchema>(`/python/runtimes/${runtimeId}`),
    enabled: Boolean(runtimeId),
    staleTime: 10 * 1000,
  });
}

/** Starts a new Docker-sandboxed Python runtime, optionally attached to a workspace. */
export function useCreatePythonRuntime() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workspaceId?: string) =>
      apiClient.post<PythonRuntimeSchema>(
        `/python/runtimes${workspaceId ? `?workspace_id=${encodeURIComponent(workspaceId)}` : ""}`,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pythonRuntimesQueryKey() });
    },
  });
}
