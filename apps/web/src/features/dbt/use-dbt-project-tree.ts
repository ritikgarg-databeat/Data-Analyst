import { useQuery } from "@tanstack/react-query";
import type { ProjectTreeItemSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function dbtProjectTreeQueryKey() {
  return ["dbt", "project-tree"] as const;
}

/** Lists every real file in the dbt project (staging/intermediate/marts/seeds/snapshots/macros/tests/analyses). */
export function useDbtProjectTree() {
  return useQuery({
    queryKey: dbtProjectTreeQueryKey(),
    queryFn: () => apiClient.get<ProjectTreeItemSchema[]>("/dbt/project-tree"),
    staleTime: 30 * 1000,
  });
}
