import { useMutation } from "@tanstack/react-query";
import type { SubmitAssessmentRequest, SubmitAssessmentResponse } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Submits all answers for an in-progress assessment attempt and returns the graded results. */
export function useSubmitAssessment(slug: string, attemptId: string) {
  return useMutation({
    mutationFn: (body: SubmitAssessmentRequest) =>
      apiClient.post<SubmitAssessmentResponse>(
        `/assessments/${slug}/attempts/${attemptId}/submit`,
        body,
      ),
  });
}
