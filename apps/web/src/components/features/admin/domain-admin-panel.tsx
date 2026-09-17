"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plus } from "lucide-react";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import type { CreateDomainRequest, Domain, UpdateDomainRequest } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { domainsQueryKey, useDomains } from "@/features/domains/use-domains";
import { apiClient } from "@/lib/api-client";

const domainSchema = z.object({
  slug: z.string().trim().min(1, "Required").regex(/^[a-z0-9-]+$/, "Lowercase letters, numbers, hyphens only"),
  name: z.string().trim().min(1, "Required"),
  description: z.string().trim().optional(),
  icon: z.string().trim().optional(),
  display_order: z.number().int().min(0),
});
type DomainFormValues = z.infer<typeof domainSchema>;

function useCreateDomain() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CreateDomainRequest) => apiClient.post<Domain>("/domains", body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: domainsQueryKey }),
  });
}

function useUpdateDomain() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateDomainRequest }) =>
      apiClient.patch<Domain>(`/domains/${id}`, body),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: domainsQueryKey }),
  });
}

function CreateDomainForm({ onDone }: { onDone: () => void }) {
  const createDomain = useCreateDomain();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<DomainFormValues>({ resolver: zodResolver(domainSchema), defaultValues: { display_order: 0 } });

  const onSubmit = handleSubmit((values) => {
    createDomain.mutate(values, { onSuccess: onDone });
  });

  return (
    <form onSubmit={onSubmit} className="grid grid-cols-1 gap-3 rounded-lg border border-border p-4 sm:grid-cols-2">
      <div className="flex flex-col gap-1">
        <Label htmlFor="domain-slug">Slug</Label>
        <Input id="domain-slug" {...register("slug")} aria-invalid={Boolean(errors.slug)} />
        {errors.slug ? <p className="text-xs text-destructive">{errors.slug.message}</p> : null}
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="domain-name">Name</Label>
        <Input id="domain-name" {...register("name")} aria-invalid={Boolean(errors.name)} />
        {errors.name ? <p className="text-xs text-destructive">{errors.name.message}</p> : null}
      </div>
      <div className="flex flex-col gap-1 sm:col-span-2">
        <Label htmlFor="domain-description">Description</Label>
        <Input id="domain-description" {...register("description")} />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="domain-icon">Icon (lucide-react name)</Label>
        <Input id="domain-icon" {...register("icon")} />
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="domain-order">Display order</Label>
        <Input id="domain-order" type="number" {...register("display_order", { valueAsNumber: true })} />
      </div>
      <div className="flex items-center gap-2 sm:col-span-2">
        <Button type="submit" size="sm" disabled={createDomain.isPending}>
          {createDomain.isPending ? "Creating..." : "Create domain"}
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={onDone}>
          Cancel
        </Button>
        {createDomain.isError ? <span className="text-xs text-destructive">Couldn&apos;t create domain.</span> : null}
      </div>
    </form>
  );
}

export function DomainAdminPanel() {
  const { data: domains, isLoading, isError, refetch } = useDomains();
  const updateDomain = useUpdateDomain();
  const [showCreate, setShowCreate] = useState(false);

  if (isLoading) return <LoadingState count={3} itemClassName="h-12" />;
  if (isError) {
    return (
      <ErrorState title="Unable to load domains" message="We couldn't reach the API." retry={() => void refetch()} />
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{domains?.length ?? 0} domains</p>
        <Button size="sm" variant="outline" onClick={() => setShowCreate((v) => !v)}>
          <Plus className="size-4" aria-hidden="true" />
          New Domain
        </Button>
      </div>

      {showCreate ? <CreateDomainForm onDone={() => setShowCreate(false)} /> : null}

      <div className="divide-y divide-border rounded-lg border border-border">
        {(domains ?? []).map((domain) => (
          <div key={domain.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
            <div>
              <p className="text-sm font-medium text-foreground">
                {domain.name} <span className="text-xs text-muted-foreground">({domain.slug})</span>
              </p>
              <p className="text-xs text-muted-foreground">
                {domain.module_count} modules · order {domain.display_order}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={domain.is_active ? "success" : "outline"}>
                {domain.is_active ? "Active" : "Inactive"}
              </Badge>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => updateDomain.mutate({ id: domain.id, body: { is_active: !domain.is_active } })}
              >
                {domain.is_active ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
