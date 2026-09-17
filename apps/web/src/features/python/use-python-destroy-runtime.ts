import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

import { pythonRuntimesQueryKey } from "./use-python-runtimes";

/** Stops and removes a runtime's sandbox container. */
export function useDestroyPythonRuntime() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (runtimeId: string) => apiClient.delete<void>(`/python/runtimes/${runtimeId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: pythonRuntimesQueryKey() });
    },
  });
}
