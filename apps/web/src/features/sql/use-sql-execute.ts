import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { ExecuteSqlRequest, SqlExecutionResultSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

import { sqlHistoryQueryKeyPrefix } from "./use-sql-history";

/** Runs a SQL query against one engine/database. Always resolves (even on a query error — check `status`). */
export function useSqlExecute() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: ExecuteSqlRequest) => apiClient.post<SqlExecutionResultSchema>("/sql/execute", body),
    onSuccess: () => {
      // Every execution (success or error) is recorded server-side as a history entry.
      void queryClient.invalidateQueries({ queryKey: sqlHistoryQueryKeyPrefix() });
    },
  });
}
