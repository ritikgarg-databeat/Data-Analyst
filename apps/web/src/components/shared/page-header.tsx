"use client";

import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { LayoutDashboard } from "lucide-react";
import { usePathname } from "next/navigation";
import type { SectionColor } from "@data-analyst-lab/shared";
import { motion } from "framer-motion";

import { findNavMatch } from "@/lib/nav-lookup";
import { sectionColorClasses } from "@/lib/section-colors";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  /** Overrides the icon auto-detected from the current route's nav entry. */
  icon?: LucideIcon;
  /** Overrides the section color auto-detected from the current route's nav entry. */
  color?: SectionColor;
  className?: string;
}

/**
 * Standard page header — colorful icon chip + title/subtitle/action, used at
 * the top of every feature page. The icon and accent color are auto-detected
 * from the current route against NAV_SECTIONS (see lib/nav-lookup.ts) so
 * every existing `<PageHeader title=".." subtitle=".." />` call site picks
 * up its section's identity for free; pass `icon`/`color` explicitly only
 * when a page's content (e.g. a specific case/project's own title) shouldn't
 * just inherit its route's default.
 */
export function PageHeader({ title, subtitle, action, icon, color, className }: PageHeaderProps) {
  const pathname = usePathname();
  const needsLookup = !icon || !color;
  const match = needsLookup ? findNavMatch(pathname) : null;
  const Icon = icon ?? match?.icon ?? LayoutDashboard;
  const resolvedColor = color ?? match?.color ?? "violet";
  const classes = sectionColorClasses(resolvedColor);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={cn("mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between", className)}
    >
      <div className="flex min-w-0 items-start gap-3 sm:gap-3.5">
        <span
          className={cn(
            "flex size-11 shrink-0 items-center justify-center rounded-xl shadow-sm",
            classes.chip,
          )}
        >
          <Icon className="size-5.5" aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <h1 className="text-xl font-semibold tracking-tight break-words text-foreground min-[380px]:text-2xl">{title}</h1>
          {subtitle ? <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{subtitle}</p> : null}
        </div>
      </div>
      {action ? <div className="flex w-full flex-wrap items-center gap-2 [&>*]:max-w-full [&>*]:flex-wrap sm:w-auto sm:shrink-0 sm:justify-end">{action}</div> : null}
    </motion.div>
  );
}
