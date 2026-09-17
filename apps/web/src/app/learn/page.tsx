"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { GraduationCap, Search, X } from "lucide-react";
import type { SearchResultKind } from "@data-analyst-lab/shared";

import { SearchResultsList } from "@/components/features/curriculum/search-results-list";
import { DomainCard } from "@/components/features/domains/domain-card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDomains } from "@/features/domains/use-domains";
import { useDebouncedValue } from "@/features/search/use-debounced-value";
import { useSearch } from "@/features/search/use-search";

const SEARCH_KINDS: SearchResultKind[] = ["domain", "module", "lesson"];

export default function LearnPage() {
  const [searchInput, setSearchInput] = useState("");
  const debouncedQuery = useDebouncedValue(searchInput, 300);
  const isSearching = debouncedQuery.trim().length > 0;
  const searchInputRef = useRef<HTMLInputElement>(null);

  const { data: domains, isLoading, isError, refetch } = useDomains();
  const searchQuery = useSearch(debouncedQuery, SEARCH_KINDS);

  // "/" focuses the search box, unless the user is already typing somewhere.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key !== "/") return;
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || target?.isContentEditable) return;
      event.preventDefault();
      searchInputRef.current?.focus();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div>
      <PageHeader
        title="Learn"
        subtitle="Browse every domain in the curriculum, from SQL fundamentals to the modern data stack."
      />

      <div className="relative mb-6 max-w-md">
        <Search
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <Input
          ref={searchInputRef}
          type="search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Search lessons..."
          aria-label="Search the curriculum"
          className="pl-9 pr-9"
        />
        {searchInput ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute top-1/2 right-1 size-7 -translate-y-1/2"
            onClick={() => setSearchInput("")}
            aria-label="Clear search"
          >
            <X className="size-4" />
          </Button>
        ) : null}
      </div>

      {isSearching ? (
        searchQuery.isLoading ? (
          <LoadingState count={5} itemClassName="h-16" />
        ) : searchQuery.isError ? (
          <ErrorState
            title="Search failed"
            message="We couldn't reach the API to search the curriculum."
            retry={() => void searchQuery.refetch()}
          />
        ) : (
          <SearchResultsList results={searchQuery.data?.results ?? []} query={debouncedQuery} />
        )
      ) : isLoading ? (
        <LoadingState count={6} className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" itemClassName="h-40" />
      ) : isError ? (
        <ErrorState
          title="Unable to load domains"
          message="We couldn't reach the API to load the curriculum. Make sure the backend is running."
          retry={() => void refetch()}
        />
      ) : !domains || domains.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="No domains yet"
          description="Curriculum content will appear here once domains are seeded on the backend."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {domains.map((domain) => (
            <Link
              key={domain.id}
              href={`/learn/${domain.slug}`}
              className="block rounded-xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <DomainCard domain={domain} progressPercent={domain.progress_percent} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
