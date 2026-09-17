"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import type { CreateModuleRequest, Module, UpdateModuleRequest } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { domainModulesQueryKey, useDomainModules } from "@/features/domains/use-domain-modules";
import { useDomains } from "@/features/domains/use-domains";
import { apiClient } from "@/lib/api-client";

const moduleSchema = z.object({
  domain_id: z.string().min(1, "Required"),
  slug: z.string().trim().min(1, "Required").regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, hyphens only"),
  title: z.string().trim().min(1, "Required"),
  description: z.string().trim().optional(),
  display_order: z.number().int().min(0),
});
type ModuleFormValues = z.infer<typeof moduleSchema>;

export function ModuleAdminPanel() {
  const { data: domains, isLoading: domainsLoading, isError: domainsError } = useDomains();
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);
  const domainSlug = selectedDomain ?? domains?.[0]?.slug ?? null;
  const modulesQuery = useDomainModules(domainSlug ?? "");
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);

  const invalidate = () => void queryClient.invalidateQueries({ queryKey: domainModulesQueryKey(domainSlug ?? "") });

  const createModule = useMutation({
    mutationFn: (body: CreateModuleRequest) => apiClient.post<Module>("/modules", body),
    onSuccess: invalidate,
  });
  const updateModule = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateModuleRequest }) =>
      apiClient.patch<Module>(`/modules/${id}`, body),
    onSuccess: invalidate,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ModuleFormValues>({ resolver: zodResolver(moduleSchema), defaultValues: { display_order: 0 } });

  const onSubmit = handleSubmit((values) => {
    createModule.mutate(values, { onSuccess: () => setShowCreate(false) });
  });

  if (domainsLoading) return <LoadingState count={3} itemClassName="h-12" />;
  if (domainsError || !domains) {
    return <ErrorState title="Unable to load domains" message="We couldn't reach the API." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Label htmlFor="module-domain-filter" className="text-xs">
            Domain
          </Label>
          <select
            id="module-domain-filter"
            value={domainSlug ?? ""}
            onChange={(event) => setSelectedDomain(event.target.value)}
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
          >
            {domains.map((domain) => (
              <option key={domain.id} value={domain.slug}>
                {domain.name}
              </option>
            ))}
          </select>
        </div>
        <Button size="sm" variant="outline" onClick={() => setShowCreate((v) => !v)}>
          <Plus className="size-4" aria-hidden="true" />
          New Module
        </Button>
      </div>

      {showCreate ? (
        <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 rounded-lg border border-border p-4 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <Label htmlFor="module-domain">Domain</Label>
            <select
              id="module-domain"
              {...register("domain_id")}
              defaultValue={domains.find((d) => d.slug === domainSlug)?.id}
              className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
            >
              {domains.map((domain) => (
                <option key={domain.id} value={domain.id}>
                  {domain.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="module-slug">Slug</Label>
            <Input id="module-slug" {...register("slug")} aria-invalid={Boolean(errors.slug)} />
            {errors.slug ? <p className="text-xs text-destructive">{errors.slug.message}</p> : null}
          </div>
          <div className="flex flex-col gap-1 sm:col-span-2">
            <Label htmlFor="module-title">Title</Label>
            <Input id="module-title" {...register("title")} aria-invalid={Boolean(errors.title)} />
            {errors.title ? <p className="text-xs text-destructive">{errors.title.message}</p> : null}
          </div>
          <div className="flex flex-col gap-1 sm:col-span-2">
            <Label htmlFor="module-description">Description</Label>
            <Input id="module-description" {...register("description")} />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="module-order">Display order</Label>
            <Input id="module-order" type="number" {...register("display_order", { valueAsNumber: true })} />
          </div>
          <div className="flex items-center gap-2 sm:col-span-2">
            <Button type="submit" size="sm" disabled={createModule.isPending}>
              {createModule.isPending ? "Creating..." : "Create module"}
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : null}

      {modulesQuery.isLoading ? (
        <LoadingState count={3} itemClassName="h-12" />
      ) : modulesQuery.isError ? (
        <ErrorState title="Unable to load modules" message="We couldn't reach the API." />
      ) : (
        <div className="divide-y divide-border rounded-lg border border-border">
          {(modulesQuery.data ?? []).map((mod) => (
            <div key={mod.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-foreground">
                  {mod.title} <span className="text-xs text-muted-foreground">({mod.slug})</span>
                </p>
                <p className="text-xs text-muted-foreground">
                  {mod.lesson_count} lessons · order {mod.display_order}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={mod.is_active ? "success" : "outline"}>{mod.is_active ? "Active" : "Inactive"}</Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => updateModule.mutate({ id: mod.id, body: { is_active: !mod.is_active } })}
                >
                  {mod.is_active ? "Deactivate" : "Activate"}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
