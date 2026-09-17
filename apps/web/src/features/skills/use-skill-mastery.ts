import { useQuery } from "@tanstack/react-query";
import type { UserSkill } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const skillMasteryQueryKey = ["skills", "mastery"] as const;

/** Every skill with the current user's mastery data (untouched skills come back at 0). */
export function useSkillMastery() {
  return useQuery({
    queryKey: skillMasteryQueryKey,
    queryFn: () => apiClient.get<UserSkill[]>("/skills/mastery"),
    staleTime: 30 * 1000,
    retry: 1,
  });
}
