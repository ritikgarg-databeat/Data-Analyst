import { useMutation } from "@tanstack/react-query";
import type {
  CorrelationTestRequest,
  RegressionRequest,
  RegressionResponse,
  StatTestRequest,
  SummaryStatsRequest,
  SummaryStatsResponse,
  TestResultResponse,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** All Statistics tools (spec section 57) are stateless computations — modeled as
 * mutations (a "Run"/"Calculate" click), not queries, since there's nothing to cache
 * or invalidate. */

export function useComputeSummary() {
  return useMutation({
    mutationFn: (payload: SummaryStatsRequest) => apiClient.post<SummaryStatsResponse>("/statistics/summary", payload),
  });
}

export function useRunStatTest() {
  return useMutation({
    mutationFn: (payload: StatTestRequest) => apiClient.post<TestResultResponse>("/statistics/test", payload),
  });
}

export function useRunCorrelationTest() {
  return useMutation({
    mutationFn: (payload: CorrelationTestRequest) =>
      apiClient.post<TestResultResponse>("/statistics/correlation", payload),
  });
}

export function useRunRegression() {
  return useMutation({
    mutationFn: (payload: RegressionRequest) => apiClient.post<RegressionResponse>("/statistics/regression", payload),
  });
}
