"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus, Trash2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import type { CreateTagRequest, Tag } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { tagsQueryKey, useTags } from "@/features/tags/use-tags";
import { apiClient } from "@/lib/api-client";

const tagSchema = z.object({
  slug: z.string().trim().min(1, "Required").regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, hyphens only"),
  name: z.string().trim().min(1, "Required"),
});
type TagFormValues = z.infer<typeof tagSchema>;

export function TagAdminPanel() {
  const { data: tags, isLoading, isError, refetch } = useTags();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);

  const createTag = useMutation({
    mutationFn: (body: CreateTagRequest) => apiClient.post<Tag>("/tags", body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: tagsQueryKey }),
  });
  const deleteTag = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/tags/${id}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: tagsQueryKey }),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TagFormValues>({ resolver: zodResolver(tagSchema) });

  const onSubmit = handleSubmit((values) => {
    createTag.mutate(values, {
      onSuccess: () => {
        reset();
        setShowCreate(false);
      },
    });
  });

  if (isLoading) return <LoadingState count={3} itemClassName="h-10" />;
  if (isError) {
    return <ErrorState title="Unable to load tags" message="We couldn't reach the API." retry={() => void refetch()} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{tags?.length ?? 0} tags</p>
        <Button size="sm" variant="outline" onClick={() => setShowCreate((v) => !v)}>
          <Plus className="size-4" aria-hidden="true" />
          New Tag
        </Button>
      </div>

      {showCreate ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3 rounded-lg border border-border p-4">
          <div className="flex flex-col gap-1">
            <Label htmlFor="tag-slug">Slug</Label>
            <Input id="tag-slug" {...register("slug")} aria-invalid={Boolean(errors.slug)} />
            {errors.slug ? <p className="text-xs text-destructive">{errors.slug.message}</p> : null}
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="tag-name">Name</Label>
            <Input id="tag-name" {...register("name")} aria-invalid={Boolean(errors.name)} />
            {errors.name ? <p className="text-xs text-destructive">{errors.name.message}</p> : null}
          </div>
          <Button type="submit" size="sm" disabled={createTag.isPending}>
            {createTag.isPending ? "Creating..." : "Create"}
          </Button>
          <Button type="button" size="sm" variant="ghost" onClick={() => setShowCreate(false)}>
            Cancel
          </Button>
        </form>
      ) : null}

      <div className="flex flex-wrap gap-2">
        {(tags ?? []).map((tag) => (
          <span
            key={tag.id}
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card py-1 pr-1 pl-3 text-xs"
          >
            {tag.name}
            <button
              type="button"
              onClick={() => deleteTag.mutate(tag.id)}
              aria-label={`Delete tag ${tag.name}`}
              className="rounded-full p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            >
              <Trash2 className="size-3" aria-hidden="true" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
