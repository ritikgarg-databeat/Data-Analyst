"use client";

import * as React from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { NAV_SECTIONS } from "@data-analyst-lab/shared";

import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { getLucideIcon } from "@/lib/icons";
import { cn } from "@/lib/utils";

interface PaletteEntry {
  id: string;
  label: string;
  group: string;
  href: string;
  icon: string;
}

/**
 * Concrete quick actions with verified destinations — each just navigates to
 * a real page where the actual action lives (no destination is invented):
 * starting a mock interview requires picking a template first, so it goes to
 * the templates catalog rather than blindly POSTing /interviews.
 */
const QUICK_ACTIONS: PaletteEntry[] = [
  { id: "action-mock-interview", label: "Start Mock Interview", group: "Quick Actions", href: "/interview/templates", icon: "Mic" },
  { id: "action-ai-mentor", label: "Ask AI Mentor", group: "Quick Actions", href: "/ai/mentor", icon: "Bot" },
  { id: "action-dataset-hub", label: "Open Dataset Hub", group: "Quick Actions", href: "/datasets", icon: "Database" },
  { id: "action-analyze-jd", label: "Analyze a Job Description", group: "Quick Actions", href: "/career/job-descriptions", icon: "FileText" },
  { id: "action-career-report", label: "Open Career Report", group: "Quick Actions", href: "/career/analytics", icon: "LineChart" },
];

function buildNavEntries(): PaletteEntry[] {
  const entries: PaletteEntry[] = [];
  for (const section of NAV_SECTIONS) {
    for (const item of section.items) {
      entries.push({
        id: `nav-${item.href}`,
        label: `Go to ${item.label}`,
        group: section.label,
        href: item.href,
        icon: item.icon,
      });
    }
  }
  return entries;
}

const ALL_ENTRIES: PaletteEntry[] = [...QUICK_ACTIONS, ...buildNavEntries()];

interface CommandPaletteContextValue {
  openPalette: () => void;
}

const CommandPaletteContext = React.createContext<CommandPaletteContextValue | null>(null);

/** Access the global command palette (e.g. to add a "Search (Ctrl/Cmd+K)" trigger button elsewhere). */
export function useCommandPalette(): CommandPaletteContextValue {
  const ctx = React.useContext(CommandPaletteContext);
  if (!ctx) throw new Error("useCommandPalette must be used within a CommandPaletteProvider");
  return ctx;
}

/**
 * Global command palette (Phase 12) — Cmd/Ctrl+K from anywhere, built on the
 * existing Dialog primitive rather than a new `cmdk` dependency. Populated
 * with every real nav destination from NAV_SECTIONS plus a handful of
 * verified quick actions. Deliberately uses <Link> (not `next/navigation`'s
 * useRouter) for navigation so it has no router-context dependency.
 */
export function CommandPaletteProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [activeIndex, setActiveIndex] = React.useState(0);
  const itemRefs = React.useRef<Array<HTMLAnchorElement | null>>([]);

  // Reset the search + selection whenever the dialog transitions to open —
  // done here (the single place `open` ever changes), not in a `useEffect`
  // keyed on `open`, so this never fires setState synchronously inside an
  // effect body.
  const handleOpenChange = React.useCallback((nextOpen: boolean) => {
    setOpen(nextOpen);
    if (nextOpen) {
      setQuery("");
      setActiveIndex(0);
    }
  }, []);

  React.useEffect(() => {
    function handleGlobalKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        handleOpenChange(!open);
      }
    }
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [open, handleOpenChange]);

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return ALL_ENTRIES;
    return ALL_ENTRIES.filter(
      (entry) => entry.label.toLowerCase().includes(q) || entry.group.toLowerCase().includes(q),
    );
  }, [query]);

  React.useEffect(() => {
    // Optional-chained on the method itself, not just the element — jsdom
    // (this project's test environment) doesn't implement `scrollIntoView`
    // at all, and a future/unusual real environment might not either.
    itemRefs.current[activeIndex]?.scrollIntoView?.({ block: "nearest" });
  }, [activeIndex]);

  const grouped = React.useMemo(() => {
    const groups = new Map<string, PaletteEntry[]>();
    for (const entry of filtered) {
      const bucket = groups.get(entry.group);
      if (bucket) bucket.push(entry);
      else groups.set(entry.group, [entry]);
    }
    return groups;
  }, [filtered]);

  function handleKeyDown(event: React.KeyboardEvent) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, filtered.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      itemRefs.current[activeIndex]?.click();
    }
  }

  let flatIndex = -1;

  return (
    <CommandPaletteContext.Provider value={{ openPalette: () => handleOpenChange(true) }}>
      {children}
      <Dialog open={open} onOpenChange={handleOpenChange}>
        <DialogContent
          size="lg"
          className="gap-0 p-0"
          onKeyDown={handleKeyDown}
          onOpenAutoFocus={(event) => {
            // Let the search input (not the dialog's close button) take focus.
            event.preventDefault();
            (event.currentTarget as HTMLElement).querySelector<HTMLInputElement>("input")?.focus();
          }}
        >
          <DialogTitle className="sr-only">Command Palette</DialogTitle>
          <DialogDescription className="sr-only">
            Search for any page or quick action across the platform.
          </DialogDescription>
          <div className="flex items-center gap-2 border-b border-border px-4 py-3">
            <Search className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            <input
              autoFocus
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setActiveIndex(0);
              }}
              placeholder="Search pages and actions..."
              aria-label="Command palette search"
              role="combobox"
              aria-expanded="true"
              aria-controls="command-palette-listbox"
              aria-activedescendant={filtered.length > 0 ? `command-palette-option-${activeIndex}` : undefined}
              className="h-6 w-full min-w-0 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
            <kbd className="hidden shrink-0 rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground sm:inline-block">
              Esc
            </kbd>
          </div>

          <div
            id="command-palette-listbox"
            role="listbox"
            aria-label="Command palette results"
            className="max-h-96 overflow-y-auto p-2"
          >
            {filtered.length === 0 ? (
              <p className="px-2 py-6 text-center text-sm text-muted-foreground">No matches.</p>
            ) : (
              Array.from(grouped.entries()).map(([group, entries]) => (
                <div key={group} className="mb-1" role="group" aria-label={group}>
                  <p className="px-2 py-1 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                    {group}
                  </p>
                  {entries.map((entry) => {
                    flatIndex += 1;
                    const index = flatIndex;
                    const isActive = index === activeIndex;
                    const Icon = getLucideIcon(entry.icon);
                    return (
                      <Link
                        key={entry.id}
                        id={`command-palette-option-${index}`}
                        href={entry.href}
                        ref={(el) => {
                          itemRefs.current[index] = el;
                        }}
                        // Not an independent tab stop — real keyboard focus
                        // stays on the search input the whole time (standard
                        // combobox/listbox pattern). Without this, Tab could
                        // move real DOM focus to an item while `activeIndex`
                        // (the only thing Enter actually activates) stayed
                        // wherever the arrow keys last left it, silently
                        // activating a DIFFERENT item than the one focused.
                        tabIndex={-1}
                        role="option"
                        aria-selected={isActive}
                        onClick={() => handleOpenChange(false)}
                        onMouseEnter={() => setActiveIndex(index)}
                        className={cn(
                          "flex items-center gap-2 rounded-md px-2 py-2 text-sm outline-none",
                          isActive ? "bg-accent text-accent-foreground" : "text-foreground hover:bg-accent/60",
                        )}
                      >
                        <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                        {entry.label}
                      </Link>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </CommandPaletteContext.Provider>
  );
}
