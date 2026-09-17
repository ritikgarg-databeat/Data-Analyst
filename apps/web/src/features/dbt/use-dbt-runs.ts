import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { DbtRunSchema, RunDbtCommandRequest } from "@data-analyst-lab/shared";

import { apiClient, ApiError } from "@/lib/api-client";
import { useToast } from "@/components/shared/toast-provider";

export function dbtRunsQueryKey() {
  return ["dbt", "runs"] as const;
}

/** Run history, most recent first. */
export function useDbtRuns(limit = 20) {
  return useQuery({
    queryKey: [...dbtRunsQueryKey(), limit] as const,
    queryFn: () => apiClient.get<DbtRunSchema[]>(`/dbt/runs?limit=${limit}`),
    staleTime: 5 * 1000,
  });
}

/** Kicks off a real `dbt <command>` invocation — see app/dbt_lab/service.py. */
export function useRunDbtCommand() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (body: RunDbtCommandRequest) => apiClient.post<DbtRunSchema>("/dbt/run", body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: dbtRunsQueryKey() });
      // A new run may have changed lineage/docs/test-results artifacts too.
      void queryClient.invalidateQueries({ queryKey: ["dbt", "lineage"] });
      void queryClient.invalidateQueries({ queryKey: ["dbt", "docs"] });
      void queryClient.invalidateQueries({ queryKey: ["dbt", "test-results"] });
    },
    // A request-level failure (API down, network drop) is distinct from a
    // dbt command that ran and failed (that's a normal DbtRun, handled by
    // the existing run-history log/badge) — without this, the Run button
    // just silently re-enabled with zero indication anything went wrong.
    onError: (error) =>
      toast({
        title: "Couldn't start the dbt run",
        description: error instanceof ApiError ? error.message : "An unexpected error occurred.",
        variant: "error",
      }),
  });
}
