"use client";

import { Search } from "lucide-react";

import { useCommandPalette } from "./command-palette";
import { MobileSidebar } from "./mobile-sidebar";
import { ThemeToggle } from "./theme-toggle";
import { UserMenu } from "./user-menu";

export function TopBar() {
  const { openPalette } = useCommandPalette();

  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/75">
      <MobileSidebar />
      <button
        type="button"
        onClick={openPalette}
        className="hidden max-w-64 flex-1 items-center gap-2 rounded-md border border-input bg-background px-3 py-1.5 text-sm text-muted-foreground shadow-sm transition-all outline-none hover:bg-accent hover:text-accent-foreground hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring sm:flex"
      >
        <Search className="size-3.5 text-section-violet" aria-hidden="true" />
        <span className="flex-1 text-left">Search...</span>
        <kbd className="rounded border border-border px-1 text-[10px]">Ctrl K</kbd>
      </button>
      <button
        type="button"
        onClick={openPalette}
        aria-label="Search"
        className="flex size-9 items-center justify-center rounded-md text-muted-foreground outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring sm:hidden"
      >
        <Search className="size-4" aria-hidden="true" />
      </button>
      <div className="flex-1" />
      <ThemeToggle />
      <UserMenu />
    </header>
  );
}
