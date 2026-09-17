import { useQuery } from "@tanstack/react-query";
import type { PythonExerciseContent } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function pythonExerciseContentQueryKey(slug: string) {
  return ["python", "exercises", slug, "content"] as const;
}

/** Fetches a Python exercise's business context, dataset files, and starter code (never the solution). */
export function usePythonExerciseContent(slug: string) {
  return useQuery({
    queryKey: pythonExerciseContentQueryKey(slug),
    queryFn: () => apiClient.get<PythonExerciseContent>(`/python/exercises/${slug}`),
    staleTime: 30 * 1000,
    retry: 1,
    enabled: Boolean(slug),
  });
}
