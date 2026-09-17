"use client";

import { useEffect, useRef, useState } from "react";
import { Clock } from "lucide-react";

import { cn } from "@/lib/utils";
import { formatSeconds } from "@/features/interview/constants";

interface InterviewTimerProps {
  /** Null means untimed (Practice mode) — renders an elapsed-time-only display. */
  totalTimeLimitSeconds: number | null;
  /** Server-computed total elapsed seconds as of the last fetch. */
  timeSpentSeconds: number;
  /** Server timestamp (ISO) marking the start of the CURRENT in-progress
   * period — null when not actively running (paused/not started/completed). */
  startedAt: string | null;
  isRunning: boolean;
  onTimeUp?: () => void;
}

/**
 * A purely client-side DISPLAY countdown — never the source of truth. The
 * server independently computes elapsed time from its own stored timestamps
 * and enforces the real limit (spec sections 34/58); this just gives the
 * learner a smooth, live-updating clock between server round trips, and
 * nudges a callback once when it estimates time is up so the caller can
 * re-fetch (which is what actually confirms and acts on it server-side).
 */
export function InterviewTimer({ totalTimeLimitSeconds, timeSpentSeconds, startedAt, isRunning, onTimeUp }: InterviewTimerProps) {
  const [now, setNow] = useState(() => Date.now());
  // A ref, not state — "have we already notified for this server-reported
  // period" is bookkeeping for an external callback, not something that
  // should itself trigger a re-render or need an effect to reset.
  const notifiedForRef = useRef<string | null>(null);

  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [isRunning]);

  const liveElapsed =
    isRunning && startedAt ? timeSpentSeconds + Math.max(0, Math.floor((now - new Date(startedAt).getTime()) / 1000)) : timeSpentSeconds;

  const remaining = totalTimeLimitSeconds != null ? totalTimeLimitSeconds - liveElapsed : null;

  useEffect(() => {
    if (remaining == null || remaining > 0) return;
    const period = `${startedAt ?? ""}-${timeSpentSeconds}`;
    if (notifiedForRef.current === period) return;
    notifiedForRef.current = period;
    onTimeUp?.();
  }, [remaining, startedAt, timeSpentSeconds, onTimeUp]);

  const isLow = remaining != null && remaining <= 60 && remaining > 0;
  const isUp = remaining != null && remaining <= 0;

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-sm font-medium tabular-nums",
        isUp
          ? "border-rose-300 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300"
          : isLow
            ? "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300"
            : "border-border bg-muted/40 text-foreground",
      )}
      role="timer"
      aria-live="polite"
    >
      <Clock className="size-4" aria-hidden="true" />
      {remaining != null ? (
        isUp ? (
          <span>Time&apos;s up</span>
        ) : (
          <span>{formatSeconds(remaining)} left</span>
        )
      ) : (
        <span>{formatSeconds(liveElapsed)} elapsed</span>
      )}
    </div>
  );
}
