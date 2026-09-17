"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { CheckCircle2, Lock, MessageCircleQuestion, Sparkles } from "lucide-react";

import { extractHeadings, ContentBlockRenderer } from "@/components/features/lesson-reader/content-block-renderer";
import { LessonBreadcrumb } from "@/components/features/lesson-reader/lesson-breadcrumb";
import { useBlockVisibility } from "@/components/features/lesson-reader/use-block-visibility";
import { DifficultyBadge } from "@/components/features/curriculum/difficulty-badge";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { useDomain } from "@/features/domains/use-domain";
import { useLessonContent } from "@/features/lessons/use-lesson-content";
import { useUpdateLessonPosition } from "@/features/lessons/use-lesson-position";
import { useUpsertLessonProgress } from "@/features/lessons/use-lesson-progress";
import { useModule } from "@/features/modules/use-module";

const POSITION_PING_INTERVAL_MS = 20_000;
const PROGRESS_SYNC_DEBOUNCE_MS = 4_000;

export default function LessonReaderPage() {
  const params = useParams<{ domainSlug: string; moduleSlug: string; lessonSlug: string }>();
  const { domainSlug, moduleSlug, lessonSlug } = params;
  const router = useRouter();

  const contentQuery = useLessonContent(lessonSlug);
  const lessonId = contentQuery.data?.lesson.id ?? "";
  const updatePosition = useUpdateLessonPosition(lessonSlug);
  const upsertProgress = useUpsertLessonProgress(lessonId);
  const domainQuery = useDomain(domainSlug);
  const moduleQuery = useModule(moduleSlug);

  const blocks = contentQuery.data?.blocks ?? [];
  const { registerBlockRef, topVisibleIndex, progressPercent, scrollToBlock, markSeen } =
    useBlockVisibility(blocks.length);

  const [liveStatus, setLiveStatus] = useState<string | null>(null);
  const hasRestoredPosition = useRef(false);
  const lastSyncedPercent = useRef(-1);
  const syncTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Restore the reader's scroll position once per lesson load.
  useEffect(() => {
    hasRestoredPosition.current = false;
  }, [lessonSlug]);
  useEffect(() => {
    if (hasRestoredPosition.current || !contentQuery.data) return;
    hasRestoredPosition.current = true;
    setLiveStatus(contentQuery.data.progress.status);
    const saved = contentQuery.data.progress.last_position;
    if (saved !== null) {
      const index = Number(saved);
      if (!Number.isNaN(index)) {
        markSeen(index);
        requestAnimationFrame(() => scrollToBlock(index));
      }
    }
  }, [contentQuery.data, markSeen, scrollToBlock]);

  // Periodic "still reading" ping — position + time spent.
  useEffect(() => {
    if (!contentQuery.data) return;
    const interval = setInterval(() => {
      updatePosition.mutate({
        last_position: String(topVisibleIndex),
        time_spent_delta_seconds: POSITION_PING_INTERVAL_MS / 1000,
      });
    }, POSITION_PING_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contentQuery.data, lessonSlug]);

  // Debounced progress_percent sync while reading (never requests COMPLETED on its own).
  useEffect(() => {
    if (!contentQuery.data || !lessonId) return;
    if (progressPercent === lastSyncedPercent.current) return;
    if (liveStatus === "COMPLETED") return;
    if (syncTimeoutRef.current) clearTimeout(syncTimeoutRef.current);
    syncTimeoutRef.current = setTimeout(() => {
      lastSyncedPercent.current = progressPercent;
      upsertProgress.mutate(
        { status: "IN_PROGRESS", progress_percent: progressPercent },
        { onSuccess: (updated) => setLiveStatus(updated.status) },
      );
    }, PROGRESS_SYNC_DEBOUNCE_MS);
    return () => {
      if (syncTimeoutRef.current) clearTimeout(syncTimeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progressPercent, contentQuery.data, lessonId, liveStatus]);

  // N / P keyboard navigation, scoped to this page only.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || target?.isContentEditable) return;
      if (!contentQuery.data) return;
      if ((event.key === "n" || event.key === "N") && contentQuery.data.next_lesson) {
        router.push(`/learn/${domainSlug}/${moduleSlug}/${contentQuery.data.next_lesson.slug}`);
      } else if ((event.key === "p" || event.key === "P") && contentQuery.data.previous_lesson) {
        router.push(`/learn/${domainSlug}/${moduleSlug}/${contentQuery.data.previous_lesson.slug}`);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [contentQuery.data, domainSlug, moduleSlug, router]);

  if (contentQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-96" />;
  }
  if (contentQuery.isError || !contentQuery.data) {
    return (
      <ErrorState
        title="Unable to load this lesson"
        message="We couldn't reach the API to load this lesson."
        retry={() => void contentQuery.refetch()}
      />
    );
  }

  const content = contentQuery.data;
  const { lesson } = content;
  const headings = extractHeadings(content.blocks);
  const threshold = content.completion_criteria.threshold;
  const canMarkComplete = liveStatus !== "COMPLETED" && progressPercent >= threshold;

  if (content.is_locked) {
    const unmet = content.prerequisites.filter((p) => p.is_hard_blocker && !p.is_completed);
    return (
      <div className="mx-auto max-w-lg py-12 text-center">
        <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-full bg-muted">
          <Lock className="size-6 text-muted-foreground" aria-hidden="true" />
        </div>
        <h1 className="text-xl font-semibold text-foreground">Complete these first</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          &quot;{lesson.title}&quot; builds on lessons you haven&apos;t finished yet.
        </p>
        <div className="mt-6 space-y-2 text-left">
          {unmet.map((p) => (
            <Link
              key={p.lesson.id}
              href={`/learn/${p.lesson.domain_slug}/${p.lesson.module_slug}/${p.lesson.slug}`}
              className="block rounded-lg border border-border px-4 py-3 text-sm hover:bg-accent/40"
            >
              {p.lesson.title}
            </Link>
          ))}
        </div>
      </div>
    );
  }

  function handleMarkComplete() {
    upsertProgress.mutate(
      { status: "COMPLETED", progress_percent: Math.max(progressPercent, threshold) },
      { onSuccess: (updated) => setLiveStatus(updated.status) },
    );
  }

  return (
    <div className="pb-24">
      <LessonBreadcrumb
        domainSlug={domainSlug}
        domainName={domainQuery.data?.name ?? domainSlug}
        moduleSlug={moduleSlug}
        moduleTitle={moduleQuery.data?.title ?? moduleSlug}
        lessonTitle={lesson.title}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[minmax(0,1fr)_240px]">
        <div className="min-w-0 space-y-8">
          <header className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <DifficultyBadge difficulty={lesson.difficulty} />
              {liveStatus === "COMPLETED" ? (
                <Badge variant="success">
                  <CheckCircle2 className="size-3" aria-hidden="true" /> Completed
                </Badge>
              ) : null}
              <span className="text-xs text-muted-foreground">{lesson.estimated_minutes} min</span>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">{lesson.title}</h1>
            {lesson.description ? (
              <p className="max-w-2xl text-sm text-muted-foreground">{lesson.description}</p>
            ) : null}
          </header>

          {content.objectives.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Learning Objectives</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1.5 text-sm">
                  {content.objectives.map((objective, index) => (
                    <li key={index} className="flex items-start gap-2 text-foreground">
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                      {objective}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : null}

          <ContentBlockRenderer blocks={content.blocks} registerBlockRef={registerBlockRef} />

          {content.key_takeaways.length > 0 ? (
            <section>
              <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Key Takeaways</h2>
              <ul className="space-y-2 rounded-xl border border-border bg-card px-4 py-4 text-sm">
                {content.key_takeaways.map((item, index) => (
                  <li key={index} className="flex items-start gap-2 text-foreground">
                    <Sparkles className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {content.common_mistakes.length > 0 ? (
            <section>
              <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Common Mistakes</h2>
              <ul className="space-y-2 rounded-xl border border-warning/30 bg-warning/5 px-4 py-4 text-sm">
                {content.common_mistakes.map((item, index) => (
                  <li key={index} className="text-foreground">
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {content.exercises.length > 0 ? (
            <section id="exercises">
              <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Exercises</h2>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {content.exercises.map((exercise) => (
                  <Link
                    key={exercise.id}
                    href={`/practice/${exercise.slug}`}
                    className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  >
                    <Card className="h-full transition-shadow hover:shadow-md">
                      <CardHeader>
                        <CardTitle className="text-sm">{exercise.title}</CardTitle>
                      </CardHeader>
                      <CardContent className="text-xs text-muted-foreground">
                        {exercise.exercise_type.replace(/_/g, " ")} · {exercise.points} pts
                      </CardContent>
                    </Card>
                  </Link>
                ))}
              </div>
            </section>
          ) : null}

          {content.interview_questions.length > 0 ? (
            <section>
              <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Interview Questions</h2>
              <div className="space-y-3">
                {content.interview_questions.map((qa, index) => (
                  <details key={index} className="rounded-xl border border-border bg-card px-4 py-3">
                    <summary className="flex cursor-pointer items-center gap-2 text-sm font-medium text-foreground">
                      <MessageCircleQuestion className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                      {qa.question}
                    </summary>
                    <p className="mt-2 text-sm text-muted-foreground">{qa.answer}</p>
                  </details>
                ))}
              </div>
            </section>
          ) : null}

          {content.related_lessons.length > 0 ? (
            <section>
              <h2 className="mb-3 text-lg font-semibold tracking-tight text-foreground">Related Lessons</h2>
              <div className="flex flex-wrap gap-2">
                {content.related_lessons.map((related) => (
                  <Link
                    key={related.id}
                    href={`/learn/${related.domain_slug}/${related.module_slug}/${related.slug}`}
                    className="rounded-full border border-border px-3 py-1.5 text-xs text-foreground hover:bg-accent/40"
                  >
                    {related.title}
                  </Link>
                ))}
              </div>
            </section>
          ) : null}
        </div>

        {headings.length > 0 ? (
          <aside className="hidden lg:block">
            <div className="sticky top-6 rounded-xl border border-border bg-card p-4 text-sm">
              <p className="mb-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                On this page
              </p>
              <nav className="space-y-1.5">
                {headings.map((heading) => (
                  <button
                    key={heading.blockIndex}
                    type="button"
                    onClick={() => scrollToBlock(heading.blockIndex)}
                    className={
                      "block w-full truncate text-left text-muted-foreground hover:text-foreground " +
                      (heading.level === 3 ? "pl-3 text-xs" : "")
                    }
                  >
                    {heading.text}
                  </button>
                ))}
              </nav>
            </div>
          </aside>
        ) : null}
      </div>

      <div className="fixed inset-x-0 bottom-0 z-10 border-t border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Progress value={progressPercent} className="w-32" aria-label={`Reading progress: ${progressPercent}%`} />
            <span className="text-xs text-muted-foreground">{progressPercent}%</span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              disabled={!content.previous_lesson}
              onClick={() =>
                content.previous_lesson &&
                router.push(`/learn/${domainSlug}/${moduleSlug}/${content.previous_lesson.slug}`)
              }
            >
              Previous
            </Button>
            {liveStatus !== "COMPLETED" ? (
              <Button onClick={handleMarkComplete} disabled={!canMarkComplete || upsertProgress.isPending}>
                Mark Complete
              </Button>
            ) : null}
            <Button
              disabled={!content.next_lesson}
              onClick={() =>
                content.next_lesson && router.push(`/learn/${domainSlug}/${moduleSlug}/${content.next_lesson.slug}`)
              }
            >
              Continue →
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
