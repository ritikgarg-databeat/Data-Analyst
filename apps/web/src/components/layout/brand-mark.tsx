import Link from "next/link";
import { Sparkles } from "lucide-react";
import { APP_NAME } from "@data-analyst-lab/shared";

import { cn } from "@/lib/utils";

interface BrandMarkProps {
  collapsed?: boolean;
  className?: string;
}

/** App logo mark + wordmark, links back to the dashboard. */
export function BrandMark({ collapsed = false, className }: BrandMarkProps) {
  return (
    <Link
      href="/"
      className={cn(
        "group flex items-center gap-2.5 rounded-md px-1 py-1 outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
        className,
      )}
    >
      <span className="gradient-brand glow-primary flex size-8 shrink-0 items-center justify-center rounded-lg text-white transition-transform duration-300 group-hover:scale-105 group-hover:rotate-3">
        <Sparkles className="size-4" aria-hidden="true" />
      </span>
      {!collapsed ? (
        <span className="truncate text-sm font-semibold tracking-tight text-sidebar-foreground">
          {APP_NAME}
        </span>
      ) : null}
    </Link>
  );
}
