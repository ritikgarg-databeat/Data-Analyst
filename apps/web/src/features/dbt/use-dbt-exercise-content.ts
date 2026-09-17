import { useQuery } from "@tanstack/react-query";
import type { DbtExerciseContent } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function dbtExerciseContentQueryKey(slug: string) {
  return ["dbt", "exercises", slug, "content"] as const;
}

/** Fetches a dbt exercise's business context, model name, and starter SQL (never the schema.yml tests or solution). */
export function useDbtExerciseContent(slug: string) {
  return useQuery({
    queryKey: dbtExerciseContentQueryKey(slug),
    queryFn: () => apiClient.get<DbtExerciseContent>(`/dbt/exercises/${slug}`),
    staleTime: 30 * 1000,
    retry: 1,
    enabled: Boolean(slug),
  });
}
