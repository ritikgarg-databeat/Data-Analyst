"use client";

import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useSidebarStore } from "@/store/sidebar-store";

import { BrandMark } from "./brand-mark";
import { SidebarNav } from "./sidebar-nav";

/** Slide-over navigation for small screens, triggered from the top bar. */
export function MobileSidebar() {
  const isMobileOpen = useSidebarStore((state) => state.isMobileOpen);
  const setMobileOpen = useSidebarStore((state) => state.setMobileOpen);

  return (
    <Sheet open={isMobileOpen} onOpenChange={setMobileOpen}>
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        aria-label="Open navigation menu"
        onClick={() => setMobileOpen(true)}
      >
        <Menu className="size-5" />
      </Button>
      <SheetContent side="left" className="p-0">
        <SheetHeader className="h-14 flex-row items-center justify-start border-b border-sidebar-border">
          <SheetTitle className="sr-only">Navigation menu</SheetTitle>
          <BrandMark />
        </SheetHeader>
        <div className="flex-1 overflow-y-auto px-2 py-4">
          <SidebarNav onNavigate={() => setMobileOpen(false)} instanceId="mobile" />
        </div>
      </SheetContent>
    </Sheet>
  );
}
