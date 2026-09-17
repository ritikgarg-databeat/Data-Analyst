"use client";

import Link from "next/link";
import { FileSearch } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useAnalyticsCases } from "@/features/analytics-cases/use-analytics-cases";

/** The Business/Product Case Library (spec sections 33 & 44). */
export function CaseLibrary() {
  const casesQuery = useAnalyticsCases();

  if (casesQuery.isLoading) {
    return <LoadingState count={6} className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" itemClassName="h-40" />;
  }
  if (casesQuery.isError) {
    return <ErrorState title="Unable to load cases" retry={() => void casesQuery.refetch()} />;
  }
  if (!casesQuery.data || casesQuery.data.length === 0) {
    return (
      <EmptyState
        icon={FileSearch}
        title="No cases yet"
        description="Business and product analytics cases will appear here once added to the curriculum."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {casesQuery.data.map((c) => (
        <Link key={c.id} href={`/analytics-cases/${c.slug}`}>
          <Card className="h-full transition-shadow hover:shadow-md">
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold text-foreground">{c.title}</p>
                <Badge variant="secondary" className="shrink-0">
                  {c.points} pts
                </Badge>
              </div>
              {c.stakeholder ? <p className="text-xs text-muted-foreground">Stakeholder: {c.stakeholder}</p> : null}
            </CardHeader>
            <CardContent>
              <p className="line-clamp-3 text-sm text-muted-foreground">
                {c.business_context ?? c.description}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {c.tags.map((t) => (
                  <Badge key={t.slug} variant="outline">
                    {t.name}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
