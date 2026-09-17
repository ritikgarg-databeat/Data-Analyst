import { useQuery } from "@tanstack/react-query";
import type { Domain } from "@data-analyst-lab/shared";

import { apiClient, ApiError } from "@/lib/api-client";

export const domainQueryKey = (slug: string) => ["domains", slug] as const;

/** Fetches a single domain by slug, used by the domain and module pages. */
export function useDomain(slug: string) {
  return useQuery({
    queryKey: domainQueryKey(slug),
    queryFn: () => apiClient.get<Domain>(`/domains/${slug}`),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(slug),
    retry: (failureCount, error) => {
      // A 404 means the slug genuinely doesn't exist — retrying won't help.
      if (error instanceof ApiError && error.status === 404) return false;
      return failureCount < 1;
    },
  });
}
