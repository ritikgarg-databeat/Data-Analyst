import { useQuery } from "@tanstack/react-query";
import type { Skill } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const skillsQueryKey = ["skills"] as const;

/** Fetches the full skill catalog, used to render the /skills page. */
export function useSkills() {
  return useQuery({
    queryKey: skillsQueryKey,
    queryFn: () => apiClient.get<Skill[]>("/skills"),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
