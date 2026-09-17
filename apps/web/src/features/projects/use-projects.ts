import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type {
  AddProjectDatasetRequest,
  CreateProjectArtifactRequest,
  CreateProjectFromDatasetRequest,
  LinkProjectDataModelRequest,
  Project,
  ProjectArtifact,
  ProjectDataset,
  ProjectTemplate,
  SaveProjectReflectionRequest,
  StartProjectFromTemplateRequest,
  SubmitProjectRequest,
  UpdateMilestoneRequest,
  UpdateProjectDbtRefsRequest,
  UpdateProjectDocumentationRequest,
  UpdateProjectPresentationRequest,
  UpdateProjectRequest,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => apiClient.get<Project[]>("/projects"),
    staleTime: 30 * 1000,
  });
}

export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: ["projects", id],
    queryFn: () => apiClient.get<Project>(`/projects/${id}`),
    enabled: Boolean(id),
  });
}

export function useCreateProjectFromDataset() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ datasetId, payload }: { datasetId: string; payload: CreateProjectFromDatasetRequest }) =>
      apiClient.post<Project>(`/projects/from-dataset/${datasetId}`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateProject(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateProjectRequest) => apiClient.patch<Project>(`/projects/${id}`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
      void queryClient.invalidateQueries({ queryKey: ["projects", id] });
    },
  });
}

// ---------------------------------------------------------------------------
// Project Templates (Phase 8) — starting one seeds a Project's milestones[]
// ---------------------------------------------------------------------------

/** The 8 active project templates — cheap enough to fetch in full and filter/find client-side
 * (there's no "get template by id" endpoint, only by slug). */
export function useProjectTemplates() {
  return useQuery({
    queryKey: ["project-templates"],
    queryFn: () => apiClient.get<ProjectTemplate[]>("/projects/templates"),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProjectTemplate(slug: string | undefined) {
  return useQuery({
    queryKey: ["project-templates", slug],
    queryFn: () => apiClient.get<ProjectTemplate>(`/projects/templates/${slug}`),
    enabled: Boolean(slug),
  });
}

export function useStartProjectFromTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: StartProjectFromTemplateRequest) => apiClient.post<Project>("/projects/from-template", payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Milestones
// ---------------------------------------------------------------------------

/** Toggles one milestone's completion — the response is the whole Project (with
 * updated milestones[]), so we can drop it straight into the cache. */
export function useUpdateMilestone(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ milestoneId, payload }: { milestoneId: string; payload: UpdateMilestoneRequest }) =>
      apiClient.patch<Project>(`/projects/${projectId}/milestones/${milestoneId}`, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(["projects", projectId], project);
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

// ---------------------------------------------------------------------------
// Artifacts — these endpoints return just the artifact, not the whole
// project, so we invalidate the project detail query to pick up the change.
// ---------------------------------------------------------------------------

export function useCreateProjectArtifact(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateProjectArtifactRequest) =>
      apiClient.post<ProjectArtifact>(`/projects/${projectId}/artifacts`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export function useDeleteProjectArtifact(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (artifactId: string) => apiClient.delete<void>(`/projects/${projectId}/artifacts/${artifactId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Project Datasets — same shape as Artifacts (return just the sub-resource).
// ---------------------------------------------------------------------------

export function useAddProjectDataset(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AddProjectDatasetRequest) =>
      apiClient.post<ProjectDataset>(`/projects/${projectId}/datasets`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

export function useDeleteProjectDataset(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectDatasetId: string) => apiClient.delete<void>(`/projects/${projectId}/datasets/${projectDatasetId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

// ---------------------------------------------------------------------------
// Documentation / Presentation — both save the WHOLE field every time and
// return the whole Project, so we can write straight into the cache.
// ---------------------------------------------------------------------------

export function useUpdateProjectDocumentation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateProjectDocumentationRequest) =>
      apiClient.patch<Project>(`/projects/${projectId}/documentation`, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(["projects", projectId], project);
    },
  });
}

export function useUpdateProjectPresentation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateProjectPresentationRequest) =>
      apiClient.patch<Project>(`/projects/${projectId}/presentation`, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(["projects", projectId], project);
    },
  });
}

// ---------------------------------------------------------------------------
// Data Model & dbt refs
// ---------------------------------------------------------------------------

export function useLinkProjectDataModel(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LinkProjectDataModelRequest) => apiClient.patch<Project>(`/projects/${projectId}/data-model`, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(["projects", projectId], project);
    },
  });
}

export function useUpdateProjectDbtRefs(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateProjectDbtRefsRequest) => apiClient.patch<Project>(`/projects/${projectId}/dbt-refs`, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(["projects", projectId], project);
    },
  });
}

// ---------------------------------------------------------------------------
// Submission & Reflection
// ---------------------------------------------------------------------------

export function useSubmitProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SubmitProjectRequest) => apiClient.post<Project>(`/projects/${projectId}/submit`, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(["projects", projectId], project);
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useSaveProjectReflection(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SaveProjectReflectionRequest) => apiClient.patch<Project>(`/projects/${projectId}/reflection`, payload),
    onSuccess: (project) => {
      queryClient.setQueryData(["projects", projectId], project);
    },
  });
}
