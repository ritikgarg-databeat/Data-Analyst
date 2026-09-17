import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import type { RecentlyCompletedItem } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";

function formatRelativeDate(iso: string): string {
  const then = new Date(iso).getTime();
  const days = Math.floor((Date.now() - then) / 86_400_000);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 7) return `${days} days ago`;
  const weeks = Math.floor(days / 7);
  return weeks === 1 ? "1 week ago" : `${weeks} weeks ago`;
}

interface RecentlyCompletedSectionProps {
  items: RecentlyCompletedItem[];
}

export function RecentlyCompletedSection({ items }: RecentlyCompletedSectionProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon={CheckCircle2}
        title="Nothing completed yet"
        description="Finish a lesson and it'll show up here."
      />
    );
  }

  return (
    <ul className="divide-y divide-border rounded-xl border border-border bg-card">
      {items.map((item) => (
        <li key={item.lesson.id}>
          <Link
            href={`/learn/${item.lesson.domain_slug}/${item.lesson.module_slug}/${item.lesson.slug}`}
            className="flex items-center justify-between gap-3 px-4 py-3 text-sm transition-colors hover:bg-accent/40"
          >
            <span className="flex items-center gap-2 text-foreground">
              <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden="true" />
              {item.lesson.title}
            </span>
            <span className="shrink-0 text-xs text-muted-foreground">
              {formatRelativeDate(item.completed_at)}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
