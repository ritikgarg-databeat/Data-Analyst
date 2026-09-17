"use client";

import { ChevronsLeft, ChevronsRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useSidebarStore } from "@/store/sidebar-store";
import { cn } from "@/lib/utils";

import { BrandMark } from "./brand-mark";
import { SidebarNav } from "./sidebar-nav";

/** Persistent desktop sidebar. Hidden below the md breakpoint (see MobileSidebar). */
export function DesktopSidebar() {
  const isCollapsed = useSidebarStore((state) => state.isCollapsed);
  const toggleCollapsed = useSidebarStore((state) => state.toggleCollapsed);

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-svh shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-[width] duration-200 md:flex",
        isCollapsed ? "w-16" : "w-64",
      )}
    >
      <div className="flex h-14 items-center justify-between border-b border-sidebar-border px-3">
        <BrandMark collapsed={isCollapsed} />
      </div>
      <div className="flex-1 overflow-y-auto px-2 py-4">
        <SidebarNav collapsed={isCollapsed} />
      </div>
      <div className="border-t border-sidebar-border p-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "w-full text-sidebar-foreground/70 hover:text-sidebar-foreground",
                isCollapsed && "justify-center px-0",
              )}
              onClick={toggleCollapsed}
              aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isCollapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
              {!isCollapsed ? <span>Collapse</span> : null}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="right">{isCollapsed ? "Expand sidebar" : "Collapse sidebar"}</TooltipContent>
        </Tooltip>
      </div>
    </aside>
  );
}
