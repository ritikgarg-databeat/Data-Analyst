import { useQuery } from "@tanstack/react-query";
import type { Domain } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const domainsQueryKey = ["domains"] as const;

/** Fetches every learning domain, used to render the /learn catalog. */
export function useDomains() {
  return useQuery({
    queryKey: domainsQueryKey,
    queryFn: () => apiClient.get<Domain[]>("/domains"),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
