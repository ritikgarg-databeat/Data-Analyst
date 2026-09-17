import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface LoadingStateProps {
  /** Number of skeleton rows/cards to render. */
  count?: number;
  className?: string;
  /** Height class applied to each skeleton block. */
  itemClassName?: string;
}

/**
 * Generic skeleton block, used while a query's data is loading. Compose it
 * inside whatever grid/list layout the destination page uses.
 */
export function LoadingState({ count = 3, className, itemClassName }: LoadingStateProps) {
  return (
    <div className={cn("grid gap-4", className)} role="status" aria-label="Loading">
      {Array.from({ length: count }).map((_, index) => (
        <Skeleton key={index} className={cn("h-28 w-full rounded-xl", itemClassName)} />
      ))}
      <span className="sr-only">Loading content…</span>
    </div>
  );
}
