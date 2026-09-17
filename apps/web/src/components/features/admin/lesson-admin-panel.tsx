"use client";

import { useState } from "react";
import { ArrowDown, ArrowUp } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Lesson, UpdateLessonAdminRequest } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useDomainModules } from "@/features/domains/use-domain-modules";
import { useDomains } from "@/features/domains/use-domains";
import { moduleLessonsQueryKey, useModuleLessons } from "@/features/modules/use-module-lessons";
import { apiClient } from "@/lib/api-client";

export function LessonAdminPanel() {
  const { data: domains } = useDomains();
  const [domainSlug, setDomainSlug] = useState<string | null>(null);
  const [moduleSlug, setModuleSlug] = useState<string | null>(null);

  const modulesQuery = useDomainModules(domainSlug ?? "");

  const effectiveModuleSlug = moduleSlug ?? modulesQuery.data?.[0]?.slug ?? null;
  const lessonsQuery = useModuleLessons(effectiveModuleSlug ?? "");
  const queryClient = useQueryClient();

  const updateLesson = useMutation({
    mutationFn: ({ id, body }: { id: string; body: UpdateLessonAdminRequest }) =>
      apiClient.patch<Lesson>(`/lessons/${id}`, body),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: moduleLessonsQueryKey(effectiveModuleSlug ?? "") }),
  });

  const lessons = [...(lessonsQuery.data ?? [])].sort((a, b) => a.display_order - b.display_order);

  function swapOrder(a: Lesson, b: Lesson) {
    updateLesson.mutate({ id: a.id, body: { display_order: b.display_order } });
    updateLesson.mutate({ id: b.id, body: { display_order: a.display_order } });
  }

  return (
    <div className="space-y-4">
      <p className="rounded-lg border border-border bg-muted/30 px-4 py-2 text-xs text-muted-foreground">
        Lesson content is authored in <code>content/lessons/</code> files — edit those and run{" "}
        <code>sync-content</code> to change titles, body, or objectives. Here you can only reorder or
        activate/deactivate.
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Label htmlFor="lesson-domain-filter" className="text-xs">
            Domain
          </Label>
          <select
            id="lesson-domain-filter"
            value={domainSlug ?? ""}
            onChange={(event) => {
              setDomainSlug(event.target.value || null);
              setModuleSlug(null);
            }}
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
          >
            <option value="">Select a domain...</option>
            {(domains ?? []).map((domain) => (
              <option key={domain.id} value={domain.slug}>
                {domain.name}
              </option>
            ))}
          </select>
        </div>

        {domainSlug ? (
          <div className="flex items-center gap-2">
            <Label htmlFor="lesson-module-filter" className="text-xs">
              Module
            </Label>
            <select
              id="lesson-module-filter"
              value={effectiveModuleSlug ?? ""}
              onChange={(event) => setModuleSlug(event.target.value)}
              className="h-9 rounded-md border border-input bg-transparent px-3 text-sm"
            >
              {(modulesQuery.data ?? []).map((mod) => (
                <option key={mod.slug} value={mod.slug}>
                  {mod.title}
                </option>
              ))}
            </select>
          </div>
        ) : null}
      </div>

      {!domainSlug ? (
        <p className="text-sm text-muted-foreground">Choose a domain and module to manage its lessons.</p>
      ) : lessonsQuery.isLoading ? (
        <LoadingState count={3} itemClassName="h-12" />
      ) : lessonsQuery.isError ? (
        <ErrorState title="Unable to load lessons" message="We couldn't reach the API." />
      ) : (
        <div className="divide-y divide-border rounded-lg border border-border">
          {lessons.map((lesson, index) => (
            <div key={lesson.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-foreground">
                  {lesson.title} <span className="text-xs text-muted-foreground">({lesson.slug})</span>
                </p>
                <p className="text-xs text-muted-foreground">display order {lesson.display_order}</p>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Move up"
                  disabled={index === 0}
                  onClick={() => swapOrder(lesson, lessons[index - 1])}
                >
                  <ArrowUp className="size-4" aria-hidden="true" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Move down"
                  disabled={index === lessons.length - 1}
                  onClick={() => swapOrder(lesson, lessons[index + 1])}
                >
                  <ArrowDown className="size-4" aria-hidden="true" />
                </Button>
                <Badge variant={lesson.is_active ? "success" : "outline"}>
                  {lesson.is_active ? "Active" : "Inactive"}
                </Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => updateLesson.mutate({ id: lesson.id, body: { is_active: !lesson.is_active } })}
                >
                  {lesson.is_active ? "Deactivate" : "Activate"}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
