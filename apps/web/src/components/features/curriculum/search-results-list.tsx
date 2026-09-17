import Link from "next/link";
import {
  BarChart3,
  BookOpen,
  Briefcase,
  FolderKanban,
  Layers,
  LayoutGrid,
  MessagesSquare,
  PenSquare,
  Search,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { SearchResultItem, SearchResultKind } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { Card, CardContent } from "@/components/ui/card";

const KIND_LABEL: Record<SearchResultKind, string> = {
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

const KIND_ICON: Record<SearchResultKind, LucideIcon> = {
  domain: LayoutGrid,
  module: Layers,
  lesson: BookOpen,
  skill: Sparkles,
  exercise: PenSquare,
  case: Briefcase,
  project: FolderKanban,
  interview_question: MessagesSquare,
  metric: BarChart3,
};

const KIND_ORDER: SearchResultKind[] = [
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

interface SearchResultsListProps {
  results: SearchResultItem[];
  query: string;
}

/** Flat list of search results, grouped by kind, each navigable via its ready-to-use url_path. */
export function SearchResultsList({ results, query }: SearchResultsListProps) {
  if (results.length === 0) {
    return (
      <EmptyState
        icon={Search}
        title="No results"
        description={`Nothing matched "${query}". Try a different search term.`}
      />
    );
  }

  const grouped = new Map<SearchResultKind, SearchResultItem[]>();
  for (const result of results) {
    const bucket = grouped.get(result.kind);
    if (bucket) {
      bucket.push(result);
    } else {
      grouped.set(result.kind, [result]);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {KIND_ORDER.filter((kind) => grouped.has(kind)).map((kind) => {
        const Icon = KIND_ICON[kind];
        return (
          <section key={kind} aria-label={KIND_LABEL[kind]}>
            <h2 className="mb-2 flex items-center gap-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
              <Icon className="size-3.5" aria-hidden="true" />
              {KIND_LABEL[kind]}
            </h2>
            <div className="flex flex-col gap-2">
              {grouped.get(kind)!.map((result) => (
                <Link
                  key={`${result.kind}-${result.id}`}
                  href={result.url_path}
                  className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                >
                  <Card className="py-3 transition-shadow hover:shadow-md">
                    <CardContent className="px-4">
                      <p className="text-sm font-medium text-foreground">{result.title}</p>
                      {result.description ? (
                        <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">{result.description}</p>
                      ) : null}
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
