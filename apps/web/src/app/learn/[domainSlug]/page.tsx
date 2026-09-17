"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { BookOpen, Compass } from "lucide-react";
import type { DifficultyLevel, LessonProgressStatus } from "@data-analyst-lab/shared";

import { CurriculumBreadcrumb } from "@/components/features/curriculum/curriculum-breadcrumb";
import { FilterGroup } from "@/components/features/curriculum/filter-group";
import { formatMinutes } from "@/components/features/curriculum/lib/format";
import { joinLessonsWithProgress } from "@/components/features/curriculum/lib/lesson-progress";
import { LessonCard } from "@/components/features/curriculum/lesson-card";
import { ModuleCard } from "@/components/features/curriculum/module-card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Progress } from "@/components/ui/progress";
import { useDomain } from "@/features/domains/use-domain";
import { useDomainModules } from "@/features/domains/use-domain-modules";
import { useModulesLessons } from "@/features/modules/use-modules-lessons";
import { useLessonProgress } from "@/features/progress/use-lesson-progress";
import { ApiError } from "@/lib/api-client";

type DifficultyFilter = DifficultyLevel | "ALL";
type StatusFilter = LessonProgressStatus | "ALL";

const DIFFICULTY_OPTIONS: { value: DifficultyFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "BEGINNER", label: "Beginner" },
  { value: "INTERMEDIATE", label: "Intermediate" },
  { value: "ADVANCED", label: "Advanced" },
];

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "NOT_STARTED", label: "Not Started" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "COMPLETED", label: "Completed" },
];

export default function DomainPage() {
  const params = useParams<{ domainSlug: string }>();
  const domainSlug = params.domainSlug;

  const [difficultyFilter, setDifficultyFilter] = useState<DifficultyFilter>("ALL");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");

  const domainQuery = useDomain(domainSlug);
  const modulesQuery = useDomainModules(domainSlug);
  const moduleSlugs = useMemo(() => (modulesQuery.data ?? []).map((mod) => mod.slug), [modulesQuery.data]);
  const lessonsQuery = useModulesLessons(moduleSlugs);
  const progressQuery = useLessonProgress();

  const moduleOrderIndex = useMemo(() => {
    const map = new Map<string, number>();
    (modulesQuery.data ?? []).forEach((mod, index) => map.set(mod.slug, index));
    return map;
  }, [modulesQuery.data]);

  const lessonsWithProgress = useMemo(
    () => joinLessonsWithProgress(lessonsQuery.lessons, progressQuery.data),
    [lessonsQuery.lessons, progressQuery.data],
  );

  const filteredLessons = useMemo(() => {
    return lessonsWithProgress
      .filter((lesson) => {
        if (difficultyFilter !== "ALL" && lesson.difficulty !== difficultyFilter) return false;
        if (statusFilter !== "ALL" && lesson.status !== statusFilter) return false;
        return true;
      })
      .sort((a, b) => {
        const orderDiff = (moduleOrderIndex.get(a.module_slug) ?? 0) - (moduleOrderIndex.get(b.module_slug) ?? 0);
        return orderDiff !== 0 ? orderDiff : a.display_order - b.display_order;
      });
  }, [lessonsWithProgress, difficultyFilter, statusFilter, moduleOrderIndex]);

  if (domainQuery.isError && domainQuery.error instanceof ApiError && domainQuery.error.status === 404) {
    return (
      <EmptyState
        icon={Compass}
        title="Domain not found"
        description="We couldn't find this domain. It may have been renamed or removed."
        action={{ label: "Back to Learn", href: "/learn" }}
      />
    );
  }

  if (domainQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-36" />;
  }

  if (domainQuery.isError || !domainQuery.data) {
    return (
      <ErrorState
        title="Unable to load this domain"
        message="We couldn't reach the API to load this domain."
        retry={() => void domainQuery.refetch()}
      />
    );
  }

  const domain = domainQuery.data;
  const totalMinutes = (modulesQuery.data ?? []).reduce((sum, mod) => sum + mod.estimated_minutes, 0);
  const rounded = Math.round(domain.progress_percent);

  return (
    <div>
      <CurriculumBreadcrumb domainSlug={domain.slug} domainName={domain.name} />

      <header className="mb-8 space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">{domain.name}</h1>
        {domain.description ? (
          <p className="max-w-2xl text-sm text-muted-foreground">{domain.description}</p>
        ) : null}
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span>
            {domain.module_count} {domain.module_count === 1 ? "module" : "modules"}
          </span>
          <span>{formatMinutes(totalMinutes)} total</span>
        </div>
        <div className="max-w-md space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Overall progress</span>
            <span>{rounded}%</span>
          </div>
          <Progress value={rounded} aria-label={`${domain.name} overall progress: ${rounded}%`} />
        </div>
      </header>

      <section className="mb-10">
        <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Modules</h2>
        {modulesQuery.isLoading ? (
          <LoadingState count={3} itemClassName="h-36" />
        ) : modulesQuery.isError ? (
          <ErrorState
            title="Unable to load modules"
            message="We couldn't reach the API to load this domain's modules."
            retry={() => void modulesQuery.refetch()}
          />
        ) : !modulesQuery.data || modulesQuery.data.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No modules yet"
            description="Modules will appear here once they're added to this domain."
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {modulesQuery.data.map((mod, index) => (
              <ModuleCard key={mod.id} module={mod} domainSlug={domain.slug} orderNumber={index + 1} />
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">All Lessons</h2>
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-6">
          <FilterGroup
            label="Difficulty"
            options={DIFFICULTY_OPTIONS}
            value={difficultyFilter}
            onChange={setDifficultyFilter}
          />
          <FilterGroup label="Status" options={STATUS_OPTIONS} value={statusFilter} onChange={setStatusFilter} />
        </div>

        {lessonsQuery.isLoading || progressQuery.isLoading ? (
          <LoadingState count={4} itemClassName="h-20" />
        ) : lessonsQuery.isError ? (
          <ErrorState
            title="Unable to load lessons"
            message="We couldn't reach the API to load lessons for this domain."
          />
        ) : filteredLessons.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No lessons match"
            description="Try a different difficulty or status filter."
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {filteredLessons.map((lesson) => (
              <LessonCard key={lesson.id} lesson={lesson} domainSlug={domain.slug} moduleSlug={lesson.module_slug} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
