import { useMutation } from "@tanstack/react-query";
import type { StartAssessmentResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Starts a NEW assessment attempt. Only call this once, from an explicit
 * "Start Assessment" click on the intro screen — never on page load, since
 * every call creates a fresh attempt server-side.
 */
export function useStartAssessment(slug: string) {
  return useMutation({
    mutationFn: () => apiClient.post<StartAssessmentResponse>(`/assessments/${slug}/attempts`),
  });
}
