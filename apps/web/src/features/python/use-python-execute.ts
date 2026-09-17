import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { ExecutePythonRequest, PythonExecutionResultSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

import { pythonHistoryQueryKeyPrefix } from "./use-python-history";
import { pythonRuntimesQueryKey } from "./use-python-runtimes";

export interface ExecutePythonVariables {
  runtimeId: string;
  body: ExecutePythonRequest;
}

/** Runs code in one runtime. Always resolves (even on a Python error — check `status`/`error`). */
export function usePythonExecute() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ runtimeId, body }: ExecutePythonVariables) =>
      apiClient.post<PythonExecutionResultSchema>(`/python/runtimes/${runtimeId}/execute`, body),
    onSuccess: () => {
      // Every execution is recorded server-side as a history entry, and moves the runtime's last_used_at.
      void queryClient.invalidateQueries({ queryKey: pythonHistoryQueryKeyPrefix() });
      void queryClient.invalidateQueries({ queryKey: pythonRuntimesQueryKey() });
    },
  });
}
