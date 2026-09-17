import { useQuery } from "@tanstack/react-query";
import type { UserProfile } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export const currentUserQueryKey = ["users", "me"] as const;

/** Fetches the (single, local) user profile. Fails gracefully if the API is offline. */
export function useCurrentUser() {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: () => apiClient.get<UserProfile>("/users/me"),
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });
}
