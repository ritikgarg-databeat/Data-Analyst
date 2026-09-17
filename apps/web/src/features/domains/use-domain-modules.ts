import { useQuery } from "@tanstack/react-query";
import type { Module } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const domainModulesQueryKey = (slug: string) => ["domains", slug, "modules"] as const;

/** Fetches every module in a domain, already sorted by display_order, for the domain page. */
export function useDomainModules(slug: string) {
  return useQuery({
    queryKey: domainModulesQueryKey(slug),
    queryFn: () => apiClient.get<Module[]>(`/domains/${slug}/modules`),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    enabled: Boolean(slug),
  });
}
