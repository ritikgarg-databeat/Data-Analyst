import { useQuery } from "@tanstack/react-query";
import type { Module } from "@data-analyst-lab/shared";

import { apiClient, ApiError } from "@/lib/api-client";

export const moduleQueryKey = (slug: string) => ["modules", slug] as const;

/** Fetches a single module by slug, used by the module page header. */
export function useModule(slug: string) {
  return useQuery({
    queryKey: moduleQueryKey(slug),
    queryFn: () => apiClient.get<Module>(`/modules/${slug}`),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(slug),
    retry: (failureCount, error) => {
      // A 404 means the slug genuinely doesn't exist — retrying won't help.
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 1;
    },
  });
}
