"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { BookOpen, ClipboardCheck, Compass } from "lucide-react";

import { CurriculumBreadcrumb } from "@/components/features/curriculum/curriculum-breadcrumb";
import { DifficultyBadge } from "@/components/features/curriculum/difficulty-badge";
import { joinLessonsWithProgress } from "@/components/features/curriculum/lib/lesson-progress";
import { LessonCard } from "@/components/features/curriculum/lesson-card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useDomain } from "@/features/domains/use-domain";
import { useModule } from "@/features/modules/use-module";
import { useModuleAssessment } from "@/features/modules/use-module-assessment";
import { useModuleLessons } from "@/features/modules/use-module-lessons";
import { useLessonProgress } from "@/features/progress/use-lesson-progress";
import { ApiError } from "@/lib/api-client";

export default function ModulePage() {
  const params = useParams<{ domainSlug: string; moduleSlug: string }>();
  const { domainSlug, moduleSlug } = params;

  const domainQuery = useDomain(domainSlug);
  const moduleQuery = useModule(moduleSlug);
  const lessonsQuery = useModuleLessons(moduleSlug);
  const progressQuery = useLessonProgress();
  const assessmentQuery = useModuleAssessment(moduleSlug, Boolean(moduleQuery.data?.has_assessment));

  const lessonsWithProgress = useMemo(
    () =>
      joinLessonsWithProgress(lessonsQuery.data ?? [], progressQuery.data).sort(
        (a, b) => a.display_order - b.display_order,
      ),
    [lessonsQuery.data, progressQuery.data],
  );

  if (moduleQuery.isError && moduleQuery.error instanceof ApiError && moduleQuery.error.status === 404) {
    return (
      <EmptyState
        icon={Compass}
        title="Module not found"
        description="We couldn't find this module. It may have been renamed or removed."
        action={{ label: "Back to Learn", href: "/learn" }}
      />
    );
  }

  if (moduleQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-36" />;
  }

  if (moduleQuery.isError || !moduleQuery.data) {
    return (
      <ErrorState
        title="Unable to load this module"
        message="We couldn't reach the API to load this module."
        retry={() => void moduleQuery.refetch()}
      />
    );
  }

  const moduleData = moduleQuery.data;
  const rounded = Math.round(moduleData.progress_percent);

  return (
    <div>
      <CurriculumBreadcrumb
        domainSlug={domainSlug}
        domainName={domainQuery.data?.name ?? domainSlug}
        moduleTitle={moduleData.title}
      />

      <header className="mb-8 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">{moduleData.title}</h1>
          <DifficultyBadge difficulty={moduleData.difficulty} />
        </div>
        {moduleData.description ? (
          <p className="max-w-2xl text-sm text-muted-foreground">{moduleData.description}</p>
        ) : null}
        <div className="flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
          <span>
            {moduleData.lesson_count} {moduleData.lesson_count === 1 ? "lesson" : "lessons"}
          </span>
          <span>{moduleData.estimated_minutes} min estimated</span>
        </div>
        <div className="max-w-md space-y-1">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Progress</span>
            <span>{rounded}%</span>
          </div>
          <Progress value={rounded} aria-label={`${moduleData.title} progress: ${rounded}%`} />
        </div>
      </header>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Lessons</h2>
        {lessonsQuery.isLoading || progressQuery.isLoading ? (
          <LoadingState count={4} itemClassName="h-20" />
        ) : lessonsQuery.isError ? (
          <ErrorState
            title="Unable to load lessons"
            message="We couldn't reach the API to load this module's lessons."
            retry={() => void lessonsQuery.refetch()}
          />
        ) : lessonsWithProgress.length === 0 ? (
          <EmptyState
            icon={BookOpen}
            title="No lessons yet"
            description="Lessons will appear here once they're added to this module."
          />
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {lessonsWithProgress.map((lesson, index) => (
              <LessonCard
                key={lesson.id}
                lesson={lesson}
                domainSlug={domainSlug}
                moduleSlug={moduleData.slug}
                previousLessonTitle={index > 0 ? lessonsWithProgress[index - 1].title : null}
              />
            ))}
          </div>
        )}
      </section>

      {moduleData.has_assessment ? (
        <section>
          <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Module Assessment</h2>
          {assessmentQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-24" />
          ) : assessmentQuery.isError || !assessmentQuery.data ? (
            <ErrorState
              title="Unable to load the assessment"
              retry={() => void assessmentQuery.refetch()}
            />
          ) : (
            <Link
              href={`/learn/${domainSlug}/${moduleData.slug}/assessment`}
              className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <Card className="transition-shadow hover:shadow-md">
                <CardHeader className="flex-row items-center gap-3">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                    <ClipboardCheck className="size-5" aria-hidden="true" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{assessmentQuery.data.title}</CardTitle>
                    {assessmentQuery.data.description ? (
                      <CardDescription>{assessmentQuery.data.description}</CardDescription>
                    ) : null}
                  </div>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">
                  {assessmentQuery.data.question_count} questions
                  {assessmentQuery.data.time_limit_minutes
                    ? ` · ${assessmentQuery.data.time_limit_minutes} min limit`
                    : ""}
                  {" · "}
                  {assessmentQuery.data.passing_score}% to pass
                </CardContent>
              </Card>
            </Link>
          )}
        </section>
      ) : null}
    </div>
  );
}
