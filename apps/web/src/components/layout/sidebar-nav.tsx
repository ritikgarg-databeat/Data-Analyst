"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_SECTIONS, sectionColor } from "@data-analyst-lab/shared";
import { motion } from "framer-motion";

import { getLucideIcon } from "@/lib/icons";
import { sectionColorClasses } from "@/lib/section-colors";
import { cn } from "@/lib/utils";

interface SidebarNavProps {
  /** Icon-only mode for the collapsed desktop sidebar. */
  collapsed?: boolean;
  /** Called when a nav link is activated — used to close the mobile sheet. */
  onNavigate?: () => void;
  /**
   * Namespaces the animated active-pill's layoutId. The desktop sidebar stays
   * mounted (just CSS-hidden) even while the mobile sheet's own SidebarNav is
   * open, so both instances exist in the tree at once — without distinct
   * ids framer-motion would try to animate one shared pill between two
   * unrelated layout boxes (one of them zero-size while hidden).
   */
  instanceId?: string;
}

function isRouteActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function SidebarNav({ collapsed = false, onNavigate, instanceId = "desktop" }: SidebarNavProps) {
  const pathname = usePathname();

  return (
    <nav aria-label="Primary" className="flex flex-col gap-5">
      {NAV_SECTIONS.map((section) => {
        const color = sectionColor(section.label);
        const classes = sectionColorClasses(color);
        return (
          <div key={section.label} className="flex flex-col gap-1">
            {!collapsed ? (
              <h2 className="flex items-center gap-1.5 px-3 text-xs font-semibold tracking-wide text-sidebar-foreground/50 uppercase">
                <span className={cn("size-1.5 rounded-full", classes.solid)} aria-hidden="true" />
                {section.label}
              </h2>
            ) : null}
            <ul className="flex flex-col gap-0.5">
              {section.items.map((item) => {
                const Icon = getLucideIcon(item.icon);
                const active = isRouteActive(pathname, item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      aria-current={active ? "page" : undefined}
                      title={collapsed ? item.label : undefined}
                      className={cn(
                        "relative flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium outline-none transition-colors",
                        "focus-visible:ring-2 focus-visible:ring-sidebar-ring",
                        active
                          ? "text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/75 hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
                        collapsed && "justify-center px-2",
                      )}
                    >
                      {active ? (
                        <motion.span
                          layoutId={`sidebar-active-pill-${instanceId}`}
                          className="absolute inset-0 rounded-md bg-sidebar-accent"
                          transition={{ type: "spring", stiffness: 500, damping: 38 }}
                        />
                      ) : null}
                      <span
                        className={cn(
                          "relative z-10 flex size-6 shrink-0 items-center justify-center rounded-md transition-colors",
                          active ? classes.chip : "text-sidebar-foreground/60",
                        )}
                      >
                        <Icon className="size-4 shrink-0" aria-hidden="true" />
                      </span>
                      {!collapsed ? <span className="relative z-10 truncate">{item.label}</span> : null}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </nav>
  );
}
