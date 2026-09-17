import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  AddEvidenceRequest,
  CreateFindingRequest,
  CreateHypothesisRequest,
  Evidence,
  Finding,
  Hypothesis,
  UpdateFindingRequest,
  UpdateHypothesisRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/**
 * Findings/Hypotheses/Evidence (Phase 8) are shared between the Case Study
 * Engine and the Project Engine — exactly one of `caseAttemptId`/`projectId`
 * identifies the owner, mirroring the backend's `Finding`/`Hypothesis`
 * columns (see app/models/finding.py). Every hook below takes the same
 * `FindingOwner` shape so the Case Workspace and Project Workspace can drop
 * in the same components/hooks unchanged.
 */
export interface FindingOwner {
  caseAttemptId?: string;
  projectId?: string;
}

function ownerParams(owner: FindingOwner): string {
  const params = new URLSearchParams();
  if (owner.caseAttemptId) params.set("case_attempt_id", owner.caseAttemptId);
  if (owner.projectId) params.set("project_id", owner.projectId);
  return params.toString();
}

function findingsQueryKey(owner: FindingOwner) {
  return ["findings", owner.caseAttemptId ?? null, owner.projectId ?? null] as const;
}

function hypothesesQueryKey(owner: FindingOwner) {
  return ["hypotheses", owner.caseAttemptId ?? null, owner.projectId ?? null] as const;
}

function isOwned(owner: FindingOwner): boolean {
  return Boolean(owner.caseAttemptId || owner.projectId);
}

// --- Findings ----------------------------------------------------------------

export function useFindings(owner: FindingOwner) {
  return useQuery({
    queryKey: findingsQueryKey(owner),
    queryFn: () => apiClient.get<Finding[]>(`/findings?${ownerParams(owner)}`),
    enabled: isOwned(owner),
  });
}

export function useCreateFinding(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Omit<CreateFindingRequest, "case_attempt_id" | "project_id">) =>
      apiClient.post<Finding>("/findings", {
        ...payload,
        case_attempt_id: owner.caseAttemptId,
        project_id: owner.projectId,
      }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: findingsQueryKey(owner) }),
  });
}

export function useUpdateFinding(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ findingId, payload }: { findingId: string; payload: UpdateFindingRequest }) =>
      apiClient.patch<Finding>(`/findings/${findingId}`, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: findingsQueryKey(owner) }),
  });
}

export function useDeleteFinding(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (findingId: string) => apiClient.delete<void>(`/findings/${findingId}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: findingsQueryKey(owner) }),
  });
}

export function useAddFindingEvidence(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ findingId, payload }: { findingId: string; payload: AddEvidenceRequest }) =>
      apiClient.post<Evidence>(`/findings/${findingId}/evidence`, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: findingsQueryKey(owner) }),
  });
}

// --- Hypotheses ----------------------------------------------------------------

export function useHypotheses(owner: FindingOwner) {
  return useQuery({
    queryKey: hypothesesQueryKey(owner),
    queryFn: () => apiClient.get<Hypothesis[]>(`/hypotheses?${ownerParams(owner)}`),
    enabled: isOwned(owner),
  });
}

export function useCreateHypothesis(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: Omit<CreateHypothesisRequest, "case_attempt_id" | "project_id">) =>
      apiClient.post<Hypothesis>("/hypotheses", {
        ...payload,
        case_attempt_id: owner.caseAttemptId,
        project_id: owner.projectId,
      }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: hypothesesQueryKey(owner) }),
  });
}

export function useUpdateHypothesis(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ hypothesisId, payload }: { hypothesisId: string; payload: UpdateHypothesisRequest }) =>
      apiClient.patch<Hypothesis>(`/hypotheses/${hypothesisId}`, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: hypothesesQueryKey(owner) }),
  });
}

export function useDeleteHypothesis(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (hypothesisId: string) => apiClient.delete<void>(`/hypotheses/${hypothesisId}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: hypothesesQueryKey(owner) }),
  });
}

export function useAddHypothesisEvidence(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ hypothesisId, payload }: { hypothesisId: string; payload: AddEvidenceRequest }) =>
      apiClient.post<Evidence>(`/hypotheses/${hypothesisId}/evidence`, payload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: hypothesesQueryKey(owner) }),
  });
}

// --- Evidence (deletable from either a finding or a hypothesis) --------------

export function useDeleteEvidence(owner: FindingOwner) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (evidenceId: string) => apiClient.delete<void>(`/evidence/${evidenceId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: findingsQueryKey(owner) });
      void queryClient.invalidateQueries({ queryKey: hypothesesQueryKey(owner) });
    },
  });
}
