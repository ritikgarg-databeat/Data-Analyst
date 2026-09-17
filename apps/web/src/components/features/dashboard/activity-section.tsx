import type { ActivityDay } from "@data-analyst-lab/shared";

import { cn } from "@/lib/utils";

interface ActivitySectionProps {
  days: ActivityDay[];
  /** Larger bars for the standalone /progress page vs. the compact dashboard widget. */
  size?: "compact" | "large";
}

const WEEKDAY_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function ActivitySection({ days, size = "compact" }: ActivitySectionProps) {
  if (days.length === 0) {
    return <p className="text-sm text-muted-foreground">No activity recorded in the last 14 days.</p>;
  }

  const maxCount = Math.max(1, ...days.map((d) => d.lessons_progressed + d.exercises_attempted));
  const barHeight = size === "large" ? "h-24" : "h-14";

  return (
    <div className="flex items-end gap-1.5">
      {days.map((day, index) => {
        const total = day.lessons_progressed + day.exercises_attempted;
        const intensity = total === 0 ? 0 : Math.max(0.15, total / maxCount);
        const date = new Date(day.date);
        const showLabel = size === "large" || index % 3 === 0 || index === days.length - 1;
        return (
          <div key={day.date} className="flex flex-1 flex-col items-center gap-1">
            <div
              className={cn("flex w-full items-end justify-center rounded-sm bg-muted", barHeight)}
              title={`${day.date}: ${day.lessons_progressed} lessons, ${day.exercises_attempted} exercises`}
            >
              <div
                className="w-full rounded-sm bg-primary transition-all"
                style={{ height: `${Math.round(intensity * 100)}%`, opacity: total === 0 ? 0 : 1 }}
              />
            </div>
            <span className="text-[10px] text-muted-foreground">
              {showLabel ? WEEKDAY_SHORT[date.getUTCDay()] : ""}
            </span>
          </div>
        );
      })}
    </div>
  );
}
