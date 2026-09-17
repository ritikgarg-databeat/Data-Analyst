"use client";

import { useState } from "react";
import { Search as SearchIcon } from "lucide-react";
import type { SearchResultKind } from "@data-analyst-lab/shared";

import { SearchResultsList } from "@/components/features/curriculum/search-results-list";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/features/search/use-debounced-value";
import { useSearch } from "@/features/search/use-search";
import { cn } from "@/lib/utils";

const ALL_KINDS: SearchResultKind[] = [
  "domain",
  "module",
  "lesson",
  "skill",
  "exercise",
  "case",
  "project",
  "interview_question",
  "metric",
];

const KIND_CHIP_LABEL: Record<SearchResultKind, string> = {
  domain: "Domains",
  module: "Modules",
  lesson: "Lessons",
  skill: "Skills",
  exercise: "Exercises",
  case: "Case Studies",
  project: "Projects",
  interview_question: "Interview Questions",
  metric: "Metrics",
};

/**
 * Global search (Phase 12) — the platform-wide counterpart to the search
 * embedded in /learn (which only covers domains/modules/lessons). Reuses the
 * existing useSearch/SearchResultsList building blocks rather than new fetch
 * logic; kind filter chips cover all 9 SearchResultKind values.
 */
export default function SearchPage() {
  const [input, setInput] = useState("");
  const debouncedQuery = useDebouncedValue(input, 300);
  const [activeKinds, setActiveKinds] = useState<Set<SearchResultKind>>(new Set(ALL_KINDS));

  // Selecting every kind is equivalent to no filter at all — omit `kind`
  // entirely in that case so the request matches a plain "search everything".
  const kindsFilter = activeKinds.size === ALL_KINDS.length ? [] : Array.from(activeKinds);
  const searchQuery = useSearch(debouncedQuery, kindsFilter);
  const isSearching = debouncedQuery.trim().length > 0;

  function toggleKind(kind: SearchResultKind) {
    setActiveKinds((current) => {
      const next = new Set(current);
      if (next.has(kind)) next.delete(kind);
      else next.add(kind);
      // Never leave every kind unselected — that reads as "search nothing".
      return next.size === 0 ? new Set(ALL_KINDS) : next;
    });
  }

  return (
    <div>
      <PageHeader
        title="Search"
        subtitle="Search across the whole platform — curriculum, skills, exercises, case studies, projects, interview questions, and metrics."
      />

      <div className="relative mb-4 max-w-xl">
        <SearchIcon
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <Input
          autoFocus
          type="search"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Search everything..."
          aria-label="Search the platform"
          className="pl-9"
        />
      </div>

      <div className="mb-6 flex flex-wrap gap-2" role="group" aria-label="Filter by result type">
        {ALL_KINDS.map((kind) => {
          const active = activeKinds.has(kind);
          return (
            <button key={kind} type="button" onClick={() => toggleKind(kind)} aria-pressed={active}>
              <Badge
                variant={active ? "default" : "outline"}
                className={cn("cursor-pointer transition-colors", !active && "text-muted-foreground")}
              >
                {KIND_CHIP_LABEL[kind]}
              </Badge>
            </button>
          );
        })}
      </div>

      {!isSearching ? (
        <EmptyState
          icon={SearchIcon}
          title="Search the platform"
          description="Start typing to search lessons, skills, exercises, case studies, projects, interview questions, and metrics all at once."
        />
      ) : searchQuery.isLoading ? (
        <LoadingState count={5} itemClassName="h-16" />
      ) : searchQuery.isError ? (
        <ErrorState
          title="Search failed"
          message="We couldn't reach the API to search the platform."
          retry={() => void searchQuery.refetch()}
        />
      ) : (
        <SearchResultsList results={searchQuery.data?.results ?? []} query={debouncedQuery} />
      )}
    </div>
  );
}
