import { useQueries } from "@tanstack/react-query";
import type { Lesson } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

import { moduleLessonsQueryKey } from "./use-module-lessons";

/**
 * Fetches lessons for several modules in parallel (one request per module —
 * a domain only ever has a handful, so this stays cheap) and flattens the
 * results into one list. Reuses the same query key shape as
 * `useModuleLessons`, so navigating from the domain page into a module page
 * serves from cache instead of refetching.
 */
export function useModulesLessons(moduleSlugs: string[]) {
  const results = useQueries({
    queries: moduleSlugs.map((slug) => ({
      queryKey: moduleLessonsQueryKey(slug),
      queryFn: () => apiClient.get<Lesson[]>(`/modules/${slug}/lessons`),
      staleTime: 5 * 60 * 1000,
      retry: 1,
    })),
  });

  const isLoading = moduleSlugs.length > 0 && results.some((result) => result.isLoading);
  const isError = results.some((result) => result.isError);
  const lessons = results.every((result) => result.data !== undefined)
    ? results.flatMap((result) => result.data ?? [])
    : [];

  return {
    lessons,
    isLoading,
    isError,
    refetch: () => {
      for (const result of results) void result.refetch();
    },
  };
}
