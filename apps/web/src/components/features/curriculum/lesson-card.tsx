import Link from "next/link";
import { Clock, Lock } from "lucide-react";
import type { LessonWithProgress } from "@data-analyst-lab/shared";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { DifficultyBadge } from "./difficulty-badge";
import { LessonStatusBadge } from "./lesson-status-badge";

interface LessonCardProps {
  lesson: LessonWithProgress;
  domainSlug: string;
  moduleSlug: string;
  /** Title of the immediately preceding lesson in the module, shown when this lesson is locked. */
  previousLessonTitle?: string | null;
}

export function LessonCard({ lesson, domainSlug, moduleSlug, previousLessonTitle }: LessonCardProps) {
  return (
    <Link
      href={`/learn/${domainSlug}/${moduleSlug}/${lesson.slug}`}
      className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      <Card className="h-full transition-shadow hover:shadow-md">
        <CardHeader className="flex-row items-start justify-between gap-3">
          <div className="min-w-0 space-y-1">
            <CardTitle className="text-sm">{lesson.title}</CardTitle>
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <DifficultyBadge difficulty={lesson.difficulty} />
              <span className="inline-flex items-center gap-1">
                <Clock className="size-3.5" aria-hidden="true" />
                {lesson.estimated_minutes} min
              </span>
            </div>
          </div>
          <LessonStatusBadge status={lesson.status} className="shrink-0" />
        </CardHeader>
        {lesson.is_locked && previousLessonTitle ? (
          <CardContent className="flex items-center gap-1.5 pt-0 text-xs text-muted-foreground">
            <Lock className="size-3.5 shrink-0" aria-hidden="true" />
            <span>Complete &ldquo;{previousLessonTitle}&rdquo; first</span>
          </CardContent>
        ) : null}
      </Card>
    </Link>
  );
}
