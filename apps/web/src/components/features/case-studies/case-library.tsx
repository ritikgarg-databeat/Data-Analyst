"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Briefcase, BarChart3, Search } from "lucide-react";
import type { CaseCategory, CaseDifficulty } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import {
  CASE_CATEGORY_LABELS,
  CASE_CATEGORY_ORDER,
  CASE_DIFFICULTY_LABELS,
  CASE_DIFFICULTY_ORDER,
} from "@/features/case-studies/constants";
import { useCases, useStartCase } from "@/features/case-studies/use-case-studies";
import { caseActionLabel } from "@/features/case-studies/utils";

/**
 * Case Studies landing page (spec section 5) — search + category/difficulty
 * filters + a card grid. The core philosophy this whole feature serves: the
 * case never reveals its solution here or on the detail page, only enough to
 * decide whether to start it.
 */
export function CaseLibrary() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<CaseCategory | "">("");
  const [difficulty, setDifficulty] = useState<CaseDifficulty | "">("");

  const casesQuery = useCases({
    search: search.trim() || undefined,
    category: category || undefined,
    difficulty: difficulty || undefined,
  });
  const startCase = useStartCase();
  const router = useRouter();

  const items = useMemo(() => casesQuery.data ?? [], [casesQuery.data]);

  function handleAction(slug: string, attemptId: string | null) {
    if (attemptId) {
      router.push(`/case-studies/attempts/${attemptId}`);
      return;
    }
    startCase.mutate(slug, {
      onSuccess: (attempt) => router.push(`/case-studies/attempts/${attempt.id}`),
    });
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search cases..."
              className="w-56 pl-8"
              aria-label="Search cases"
            />
          </div>
          <Select
            value={category}
            onChange={(event) => setCategory(event.target.value as CaseCategory | "")}
            className="w-52"
            aria-label="Filter by category"
          >
            <option value="">All categories</option>
            {CASE_CATEGORY_ORDER.map((value) => (
              <option key={value} value={value}>
                {CASE_CATEGORY_LABELS[value]}
              </option>
            ))}
          </Select>
          <Select
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value as CaseDifficulty | "")}
            className="w-40"
            aria-label="Filter by difficulty"
          >
            <option value="">All difficulties</option>
            {CASE_DIFFICULTY_ORDER.map((value) => (
              <option key={value} value={value}>
                {CASE_DIFFICULTY_LABELS[value]}
              </option>
            ))}
          </Select>
        </div>
        <Button variant="outline" size="sm" asChild>
          <Link href="/case-studies/performance">
            <BarChart3 className="size-4" aria-hidden="true" />
            My Case Performance
          </Link>
        </Button>
      </div>

      {casesQuery.isLoading ? (
        <LoadingState count={6} itemClassName="h-44" className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" />
      ) : casesQuery.isError ? (
        <ErrorState message="We couldn't reach the API to load case studies." retry={() => void casesQuery.refetch()} />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No cases match your filters"
          description="Try clearing the search box or filters above."
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map(({ case: c, attempt_id, attempt_status, attempt_score }) => (
            <div key={c.id} className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
              <div className="flex flex-wrap items-center gap-1.5">
                <Badge variant="outline">{CASE_CATEGORY_LABELS[c.category]}</Badge>
                <Badge variant="secondary">{CASE_DIFFICULTY_LABELS[c.difficulty]}</Badge>
              </div>
              <div>
                <p className="font-medium text-foreground">{c.title}</p>
                <p className="mt-1 line-clamp-3 text-sm text-muted-foreground">{c.problem_statement}</p>
              </div>
              {c.skills.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {c.skills.slice(0, 4).map((skill) => (
                    <Badge key={skill} variant="outline" className="text-[10px]">
                      {skill}
                    </Badge>
                  ))}
                </div>
              ) : null}
              <div className="mt-auto flex items-center justify-between gap-2 pt-1">
                <span className="text-xs text-muted-foreground">
                  {c.estimated_minutes} min
                  {attempt_status === "COMPLETED" && attempt_score != null ? ` · Scored ${attempt_score.toFixed(0)}%` : ""}
                </span>
                <div className="flex items-center gap-1.5">
                  <Link href={`/case-studies/${c.slug}`} className="text-xs font-medium text-primary hover:underline">
                    Details
                  </Link>
                  <Button
                    size="sm"
                    onClick={() => handleAction(c.slug, attempt_id)}
                    disabled={startCase.isPending}
                  >
                    {caseActionLabel(attempt_status)}
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
