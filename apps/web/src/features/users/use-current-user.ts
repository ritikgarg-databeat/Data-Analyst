import { useQuery } from "@tanstack/react-query";
import type { AuthUserProfile } from "@data-analyst-lab/shared";

import { apiClient, ApiError } from "@/lib/api-client";

export const currentUserQueryKey = ["users", "me"] as const;

/** Fetches the authenticated account profile. */
export function useCurrentUser(enabled = true) {
  return useQuery({
    queryKey: currentUserQueryKey,
    queryFn: () => apiClient.get<AuthUserProfile>("/users/me"),
    staleTime: 5 * 60 * 1000,
    enabled,
    retry: (failureCount, error) =>
      failureCount < 1 && error instanceof ApiError && error.isNetworkError,
  });
}
