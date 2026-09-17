import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { CreateNoteRequest, DatasetNoteSchema } from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

function notesQueryKey(idOrSlug: string | undefined) {
  return ["datasets", "detail", idOrSlug, "notes"] as const;
}

export function useDatasetNotes(idOrSlug: string | undefined) {
  return useQuery({
    queryKey: notesQueryKey(idOrSlug),
    queryFn: () => apiClient.get<DatasetNoteSchema[]>(`/datasets/${encodeURIComponent(idOrSlug!)}/notes`),
    enabled: Boolean(idOrSlug),
    staleTime: 30 * 1000,
  });
}

export function useAddNote(idOrSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateNoteRequest) =>
      apiClient.post<DatasetNoteSchema>(`/datasets/${idOrSlug}/notes`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notesQueryKey(idOrSlug) });
    },
  });
}

export function useDeleteNote(idOrSlug: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (noteId: string) => apiClient.delete<void>(`/datasets/${idOrSlug}/notes/${noteId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: notesQueryKey(idOrSlug) });
    },
  });
}
