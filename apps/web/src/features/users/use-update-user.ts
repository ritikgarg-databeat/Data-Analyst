import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { UpdateUserProfileRequest, UserProfile } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

import { currentUserQueryKey } from "./use-current-user";

/** Updates the local user's profile (currently just the display name). */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (body: UpdateUserProfileRequest) =>
      apiClient.patch<UserProfile>("/users/me", body),
    onSuccess: (updated) => {
      queryClient.setQueryData(currentUserQueryKey, updated);
    },
  });
}
