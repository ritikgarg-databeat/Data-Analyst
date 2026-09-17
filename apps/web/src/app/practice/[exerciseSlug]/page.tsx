"use client";

import { useCallback, useEffect, useRef } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ChevronRight } from "lucide-react";

import { ExerciseInteraction } from "@/components/features/exercises/exercise-interaction";

export default function StandaloneExercisePage() {
  const params = useParams<{ exerciseSlug: string }>();
  const slug = params.exerciseSlug;

  const retryRef = useRef<(() => void) | null>(null);
  const handleRetryRef = useCallback((retry: () => void) => {
    retryRef.current = retry;
  }, []);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== "r" && event.key !== "R") return;
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || target?.isContentEditable) return;
      retryRef.current?.();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="mx-auto max-w-2xl">
      <nav className="mb-4 flex items-center gap-1.5 text-sm text-muted-foreground">
        <Link href="/practice" className="hover:text-foreground hover:underline">
          Practice
        </Link>
        <ChevronRight className="size-3.5" aria-hidden="true" />
        <span className="text-foreground">{slug}</span>
      </nav>

      <ExerciseInteraction slug={slug} onRetryRef={handleRetryRef} />
    </div>
  );
}
