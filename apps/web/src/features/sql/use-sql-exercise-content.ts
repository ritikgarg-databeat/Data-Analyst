import { useQuery } from "@tanstack/react-query";
import type { SqlExerciseContent } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function sqlExerciseContentQueryKey(slug: string) {
  return ["sql", "exercises", slug, "content"] as const;
}

/** Fetches a SQL exercise's business context, table summaries, and starter query (never the solution). */
export function useSqlExerciseContent(slug: string) {
  return useQuery({
    queryKey: sqlExerciseContentQueryKey(slug),
    queryFn: () => apiClient.get<SqlExerciseContent>(`/sql/exercises/${slug}`),
    staleTime: 30 * 1000,
    retry: 1,
    enabled: Boolean(slug),
  });
}
