"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { LoadingState } from "@/components/shared/loading-state";
import { PageHeader } from "@/components/shared/page-header";
import { useKnowledgeSearch } from "@/features/ai/use-ai";

/**
 * Ask the Knowledge Base (spec sections 61-64) — retrieval-grounded Q&A over
 * the platform's own lesson/metric content (a lightweight local TF-IDF RAG,
 * see app/ai/retrieval.py), with citations linking back to the real lesson.
 * Never answers from general model knowledge — says so when retrieval finds
 * nothing relevant.
 */
export function KnowledgeSearchPage() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const searchQuery = useKnowledgeSearch(submittedQuery);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setSubmittedQuery(query.trim());
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader
        title="Ask the Knowledge Base"
        subtitle="Retrieval-grounded answers from this platform's own lessons and metric definitions — never from general AI knowledge."
      />

      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="e.g. What's the difference between retention and churn?"
          className="max-w-xl"
        />
        <Button type="submit" disabled={!query.trim() || searchQuery.isFetching}>
          <Search className="size-4" aria-hidden="true" />
          {searchQuery.isFetching ? "Searching..." : "Ask"}
        </Button>
      </form>

      {searchQuery.isFetching ? <LoadingState count={1} itemClassName="h-32" /> : null}

      {searchQuery.data ? (
        <Card className="max-w-2xl">
          <CardContent className="flex flex-col gap-4 pt-6">
            {searchQuery.data.insufficient_knowledge ? (
              <p className="text-sm text-muted-foreground">{searchQuery.data.answer}</p>
            ) : (
              <>
                <p className="text-sm whitespace-pre-wrap text-foreground">{searchQuery.data.answer}</p>
                {searchQuery.data.sources.length > 0 ? (
                  <div>
                    <p className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">Sources</p>
                    <ul className="mt-1 flex flex-col gap-1">
                      {searchQuery.data.sources.map((source, index) => (
                        <li key={index} className="text-sm">
                          {source.lesson_slug && source.domain_slug && source.module_slug ? (
                            <Link
                              href={`/learn/${source.domain_slug}/${source.module_slug}/${source.lesson_slug}`}
                              className="text-primary underline-offset-2 hover:underline"
                            >
                              {source.title}
                            </Link>
                          ) : (
                            <span className="text-foreground">{source.title}</span>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </>
            )}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
