"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Bookmark, BookmarkCheck, ListChecks, Search } from "lucide-react";
import type { InterviewQuestionType } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { INTERVIEW_QUESTION_TYPE_LABELS, INTERVIEW_QUESTION_TYPE_ORDER } from "@/features/interview/constants";
import {
  useCreateInterviewBookmark,
  useDeleteInterviewBookmark,
  useInterviewBookmarks,
  useInterviewQuestions,
} from "@/features/interview/use-interview";

const DIFFICULTIES = ["BEGINNER", "INTERMEDIATE", "ADVANCED"] as const;
const PAGE_SIZE = 24;

export function InterviewQuestionCatalog() {
  const [search, setSearch] = useState("");
  const [interviewType, setInterviewType] = useState<InterviewQuestionType | "">("");
  const [difficulty, setDifficulty] = useState<string>("");
  const [bookmarkedOnly, setBookmarkedOnly] = useState(false);
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  const filters = {
    search: search.trim() || undefined,
    interview_type: interviewType || undefined,
    difficulty: difficulty || undefined,
    bookmarked_only: bookmarkedOnly || undefined,
  };
  const questionsQuery = useInterviewQuestions(filters);
  const bookmarksQuery = useInterviewBookmarks();
  const createBookmark = useCreateInterviewBookmark();
  const deleteBookmark = useDeleteInterviewBookmark();

  const bookmarkByQuestionId = useMemo(() => {
    const map = new Map<string, string>();
    for (const b of bookmarksQuery.data ?? []) {
      if (b.target_type === "QUESTION") map.set(b.target_id, b.id);
    }
    return map;
  }, [bookmarksQuery.data]);

  function toggleBookmark(questionId: string) {
    const existingId = bookmarkByQuestionId.get(questionId);
    if (existingId) deleteBookmark.mutate(existingId);
    else createBookmark.mutate({ target_type: "QUESTION", target_id: questionId });
  }

  const allItems = questionsQuery.data ?? [];
  const items = allItems.slice(0, visibleCount);
  const filterKey = JSON.stringify(filters);
  const [lastFilterKey, setLastFilterKey] = useState(filterKey);
  if (filterKey !== lastFilterKey) {
    setLastFilterKey(filterKey);
    setVisibleCount(PAGE_SIZE);
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search questions..."
            className="w-56 pl-8"
            aria-label="Search interview questions"
          />
        </div>
        <Select value={interviewType} onChange={(e) => setInterviewType(e.target.value as InterviewQuestionType | "")} className="w-52" aria-label="Filter by type">
          <option value="">All types</option>
          {INTERVIEW_QUESTION_TYPE_ORDER.map((value) => (
            <option key={value} value={value}>
              {INTERVIEW_QUESTION_TYPE_LABELS[value]}
            </option>
          ))}
        </Select>
        <Select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} className="w-40" aria-label="Filter by difficulty">
          <option value="">All difficulties</option>
          {DIFFICULTIES.map((value) => (
            <option key={value} value={value}>
              {value.charAt(0) + value.slice(1).toLowerCase()}
            </option>
          ))}
        </Select>
        <Button
          variant={bookmarkedOnly ? "default" : "outline"}
          size="sm"
          onClick={() => setBookmarkedOnly((prev) => !prev)}
        >
          <Bookmark className="size-4" aria-hidden="true" />
          Bookmarked
        </Button>
      </div>

      {questionsQuery.isLoading ? (
        <LoadingState count={9} itemClassName="h-32" className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" />
      ) : questionsQuery.isError ? (
        <ErrorState message="We couldn't reach the API to load the question bank." retry={() => void questionsQuery.refetch()} />
      ) : allItems.length === 0 ? (
        <EmptyState icon={ListChecks} title="No questions match your filters" description="Try clearing the search box or filters above." />
      ) : (
        <>
        <p className="text-sm text-muted-foreground">
          Showing {items.length} of {allItems.length} question{allItems.length === 1 ? "" : "s"}
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((q) => (
            <div key={q.id} className="flex flex-col gap-2 rounded-xl border border-border bg-card p-4">
              <div className="flex items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-1.5">
                  <Badge variant="outline">{INTERVIEW_QUESTION_TYPE_LABELS[q.interview_type]}</Badge>
                  <Badge variant="secondary">{q.difficulty}</Badge>
                </div>
                <button
                  type="button"
                  onClick={() => toggleBookmark(q.id)}
                  aria-label={bookmarkByQuestionId.has(q.id) ? "Remove bookmark" : "Add bookmark"}
                  className="text-muted-foreground hover:text-foreground"
                >
                  {bookmarkByQuestionId.has(q.id) ? (
                    <BookmarkCheck className="size-4 text-primary" aria-hidden="true" />
                  ) : (
                    <Bookmark className="size-4" aria-hidden="true" />
                  )}
                </button>
              </div>
              <p className="font-medium text-foreground">{q.title}</p>
              <div className="mt-auto flex items-center justify-between gap-2 pt-1 text-xs text-muted-foreground">
                <span>
                  {q.time_limit_seconds ? `${Math.round(q.time_limit_seconds / 60)} min` : "Untimed"}
                  {q.best_score != null ? ` · Best ${q.best_score.toFixed(0)}%` : ""}
                </span>
                <Link href={`/interview/questions/${q.slug}`} className="font-medium text-primary hover:underline">
                  View
                </Link>
              </div>
            </div>
          ))}
        </div>
        {allItems.length > items.length ? (
          <div className="flex justify-center">
            <Button variant="outline" onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}>
              Show more
            </Button>
          </div>
        ) : null}
        </>
      )}
    </div>
  );
}
