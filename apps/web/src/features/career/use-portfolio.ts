import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  AIStructuredResponse,
  CreatePortfolioItemRequest,
  Portfolio,
  PortfolioGapEntry,
  PortfolioQualityScoreResponse,
  UpdatePortfolioItemRequest,
  UpdatePortfolioRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Portfolio Builder (Phase 11) data layer — mirrors
 * features/interview/use-interview.ts's shape. The Portfolio is a per-user
 * singleton (one profile with many items), so every mutation that returns
 * the full updated `Portfolio` writes it straight into `portfolioQueryKey`.
 */

export const portfolioQueryKey = ["portfolio"] as const;
export const portfolioQualityScoreQueryKey = ["portfolio-quality-score"] as const;
export const portfolioGapsQueryKey = (targetRoleId?: string) => ["portfolio-gaps", targetRoleId ?? null] as const;

export function usePortfolio() {
  return useQuery({
    queryKey: portfolioQueryKey,
    queryFn: () => apiClient.get<Portfolio>("/portfolio"),
  });
}

export function useUpdatePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdatePortfolioRequest) => apiClient.patch<Portfolio>("/portfolio", payload),
    onSuccess: (portfolio) => queryClient.setQueryData(portfolioQueryKey, portfolio),
  });
}

export function useCreatePortfolioItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreatePortfolioItemRequest) => apiClient.post<Portfolio>("/portfolio/items", payload),
    onSuccess: (portfolio) => {
      queryClient.setQueryData(portfolioQueryKey, portfolio);
      void queryClient.invalidateQueries({ queryKey: portfolioQualityScoreQueryKey });
    },
  });
}

export function useUpdatePortfolioItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string } & UpdatePortfolioItemRequest) =>
      apiClient.patch<Portfolio>(`/portfolio/items/${id}`, body),
    onSuccess: (portfolio) => {
      queryClient.setQueryData(portfolioQueryKey, portfolio);
      void queryClient.invalidateQueries({ queryKey: portfolioQualityScoreQueryKey });
    },
  });
}

export function useDeletePortfolioItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete<void>(`/portfolio/items/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: portfolioQueryKey });
      void queryClient.invalidateQueries({ queryKey: portfolioQualityScoreQueryKey });
    },
  });
}

export function usePortfolioQualityScore() {
  return useQuery({
    queryKey: portfolioQualityScoreQueryKey,
    queryFn: () => apiClient.get<PortfolioQualityScoreResponse>("/portfolio/quality-score"),
  });
}

/** AI-structured review of the whole portfolio — result held by the caller, no dedicated cache entry. */
export function useReviewPortfolio() {
  return useMutation({
    mutationFn: () => apiClient.post<AIStructuredResponse>("/portfolio/review"),
  });
}

export function usePortfolioGaps(targetRoleId?: string) {
  const qs = targetRoleId ? `?target_role_id=${targetRoleId}` : "";
  return useQuery({
    queryKey: portfolioGapsQueryKey(targetRoleId),
    queryFn: () => apiClient.get<PortfolioGapEntry[]>(`/portfolio/gaps${qs}`),
  });
}
