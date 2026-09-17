import { useQuery } from "@tanstack/react-query";
import type { NodeDocSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Column-level docs (types from catalog.json, descriptions from manifest.json) for every model/seed/snapshot. */
export function useDbtDocs() {
  return useQuery({
    queryKey: ["dbt", "docs"] as const,
    queryFn: () => apiClient.get<NodeDocSchema[]>("/dbt/docs"),
    staleTime: 5 * 1000,
  });
}
