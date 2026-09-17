import { useQuery } from "@tanstack/react-query";
import type { SearchResponse, SearchResultKind } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

function buildSearchPath(query: string, kinds: SearchResultKind[]): string {
  const params = new URLSearchParams();
  params.set("q", query);
  for (const kind of kinds) params.append("kind", kind);
  return `/search?${params.toString()}`;
}

/** Searches the curriculum for `query` across the given result kinds. Disabled while `query` is empty. */
export function useSearch(query: string, kinds: SearchResultKind[]) {
  const trimmed = query.trim();
  return useQuery({
    queryKey: ["search", trimmed, ...kinds],
    queryFn: () => apiClient.get<SearchResponse>(buildSearchPath(trimmed, kinds)),
    enabled: trimmed.length > 0,
    staleTime: 30 * 1000,
    retry: 1,
  });
}
