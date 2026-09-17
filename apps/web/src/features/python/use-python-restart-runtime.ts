import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { PythonRuntimeSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

import { pythonRuntimesQueryKey } from "./use-python-runtimes";

/** Restarts a runtime's sandbox container — wipes all its in-memory variables/state. */
export function useRestartPythonRuntime() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (runtimeId: string) => apiClient.post<PythonRuntimeSchema>(`/python/runtimes/${runtimeId}/restart`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pythonRuntimesQueryKey() });
    },
  });
}
