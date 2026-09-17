import type { Lesson, LessonProgress, LessonWithProgress } from "@data-analyst-lab/shared";

/**
 * Joins a lesson list with the user's per-lesson progress, and computes a
 * client-side "locked" heuristic: seeded content chains prerequisites
 * strictly sequentially within a module, so a lesson is considered locked
 * whenever the previous lesson (by display_order, within the same module)
 * isn't COMPLETED. This is a display heuristic only — the lesson reader page
 * enforces the real lock/prerequisite state via its own API call.
 */
export function joinLessonsWithProgress(
  lessons: Lesson[],
  progress: LessonProgress[] | undefined,
): LessonWithProgress[] {
  const progressByLessonId = new Map((progress ?? []).map((entry) => [entry.lesson_id, entry]));

  const withStatus: LessonWithProgress[] = lessons.map((lesson) => {
    const entry = progressByLessonId.get(lesson.id);
    return {
      ...lesson,
      status: entry?.status ?? "NOT_STARTED",
      progress_percent: entry?.progress_percent ?? 0,
      is_locked: false,
    };
  });

  const byModule = new Map<string, LessonWithProgress[]>();
  for (const lesson of withStatus) {
    const bucket = byModule.get(lesson.module_slug);
    if (bucket) {
      bucket.push(lesson);
    } else {
      byModule.set(lesson.module_slug, [lesson]);
    }
  }

  for (const bucket of byModule.values()) {
    const ordered = [...bucket].sort((a, b) => a.display_order - b.display_order);
    ordered.forEach((lesson, index) => {
      lesson.is_locked = index > 0 && ordered[index - 1].status !== "COMPLETED";
    });
  }

  return withStatus;
}
