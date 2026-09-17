import { useMutation } from "@tanstack/react-query";
import type {
  AnalyzeABTestRequest,
  AnalyzeABTestResponse,
  PowerRequest,
  PowerResponse,
  SampleSizeRequest,
  SampleSizeResponse,
  SimulateABTestRequest,
  SimulateABTestResponse,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** All Experimentation tools (spec section 57) are stateless computations —
 * modeled as mutations, not queries. */

export function useComputeSampleSize() {
  return useMutation({
    mutationFn: (payload: SampleSizeRequest) => apiClient.post<SampleSizeResponse>("/experiments/sample-size", payload),
  });
}

export function useComputePower() {
  return useMutation({
    mutationFn: (payload: PowerRequest) => apiClient.post<PowerResponse>("/experiments/power", payload),
  });
}

export function useAnalyzeABTest() {
  return useMutation({
    mutationFn: (payload: AnalyzeABTestRequest) =>
      apiClient.post<AnalyzeABTestResponse>("/experiments/analyze", payload),
  });
}

export function useSimulateABTest() {
  return useMutation({
    mutationFn: (payload: SimulateABTestRequest) =>
      apiClient.post<SimulateABTestResponse>("/experiments/simulate", payload),
  });
}
