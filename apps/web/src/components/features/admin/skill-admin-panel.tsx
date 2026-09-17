"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { SKILL_CATEGORY_LABELS, SKILL_CATEGORY_ORDER } from "@data-analyst-lab/shared";
import type { CreateSkillRequest, Skill } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { skillsQueryKey, useSkills } from "@/features/skills/use-skills";
import { apiClient } from "@/lib/api-client";

const skillSchema = z.object({
  slug: z.string().trim().min(1, "Required").regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, hyphens only"),
  name: z.string().trim().min(1, "Required"),
  description: z.string().trim().optional(),
  category: z.enum(SKILL_CATEGORY_ORDER as [string, ...string[]]),
  target_level: z.enum(["BEGINNER", "INTERMEDIATE", "ADVANCED"]),
});
type SkillFormValues = z.infer<typeof skillSchema>;

function useCreateSkill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateSkillRequest) => apiClient.post<Skill>("/skills", body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: skillsQueryKey }),
  });
}

function CreateSkillForm({ onDone }: { onDone: () => void }) {
  const createSkill = useCreateSkill();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SkillFormValues>({
    resolver: zodResolver(skillSchema),
    defaultValues: { target_level: "INTERMEDIATE", category: SKILL_CATEGORY_ORDER[0] },
  });

  const onSubmit = handleSubmit((values) => {
    createSkill.mutate(values as CreateSkillRequest, { onSuccess: onDone });
  });

  return (
    <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 rounded-lg border border-border p-4 sm:grid-cols-2">
      <div className="flex flex-col gap-1">
        <Label htmlFor="skill-slug">Slug</Label>
        <Input id="skill-slug" {...register("slug")} aria-invalid={Boolean(errors.slug)} />
        {errors.slug ? <p className="text-xs text-destructive">{errors.slug.message}</p> : null}
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="skill-name">Name</Label>
        <Input id="skill-name" {...register("name")} aria-invalid={Boolean(errors.name)} />
        {errors.name ? <p className="text-xs text-destructive">{errors.name.message}</p> : null}
      </div>
      <div className="flex flex-col gap-1 sm:col-span-2">
        <Label htmlFor="skill-description">Description</Label>
        <Input id="skill-description" {...register("description")} />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="skill-category">Category</Label>
        <select
          id="skill-category"
          {...register("category")}
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
        >
          {SKILL_CATEGORY_ORDER.map((category) => (
            <option key={category} value={category}>
              {SKILL_CATEGORY_LABELS[category]}
            </option>
          ))}
        </select>
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="skill-level">Target level</Label>
        <select
          id="skill-level"
          {...register("target_level")}
          className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
        >
          <option value="BEGINNER">Beginner</option>
          <option value="INTERMEDIATE">Intermediate</option>
          <option value="ADVANCED">Advanced</option>
        </select>
      </div>
      <div className="flex items-center gap-2 sm:col-span-2">
        <Button type="submit" size="sm" disabled={createSkill.isPending}>
          {createSkill.isPending ? "Creating..." : "Create skill"}
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        {createSkill.isError ? <span className="text-xs text-destructive">Couldn&apos;t create skill.</span> : null}
      </div>
    </form>
  );
}

export function SkillAdminPanel() {
  const { data: skills, isLoading, isError, refetch } = useSkills();
  const [showCreate, setShowCreate] = useState(false);

  if (isLoading) return <LoadingState count={3} itemClassName="h-12" />;
  if (isError) {
    return (
      <ErrorState title="Unable to load skills" message="We couldn't reach the API." retry={() => void refetch()} />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{skills?.length ?? 0} skills</p>
        <Button size="sm" variant="outline" onClick={() => setShowCreate((v) => !v)}>
          <Plus className="size-4" aria-hidden="true" />
          New Skill
        </Button>
      </div>

      {showCreate ? <CreateSkillForm onDone={() => setShowCreate(false)} /> : null}

      <div className="divide-y divide-border rounded-lg border border-border">
        {(skills ?? []).map((skill) => (
          <div key={skill.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                {skill.name} <span className="text-xs text-muted-foreground">({skill.slug})</span>
              </p>
              <p className="text-xs text-muted-foreground">
                {SKILL_CATEGORY_LABELS[skill.category]} · target {skill.target_level.toLowerCase()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
