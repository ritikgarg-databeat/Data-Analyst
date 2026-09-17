import { useQuery } from "@tanstack/react-query";
import type { Tag } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const tagsQueryKey = ["tags"] as const;

/** Every tag in the shared taxonomy — used for the Dataset Hub's tag filter/tagging UI and the Tag Admin Panel. */
export function useTags() {
  return useQuery({
    queryKey: tagsQueryKey,
    queryFn: () => apiClient.get<Tag[]>("/tags"),
    staleTime: 5 * 60 * 1000,
  });
}
