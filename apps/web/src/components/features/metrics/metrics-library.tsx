"use client";

import { useMemo, useState } from "react";
import { BarChart3, Search } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useMetrics } from "@/features/metrics/use-metrics";
import type { MetricDefinition } from "@data-analyst-lab/shared";

import { MetricDetailSheet } from "./metric-detail-sheet";

export function MetricsLibrary() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const metricsQuery = useMetrics();
  const [selected, setSelected] = useState<MetricDefinition | null>(null);

  const categories = useMemo(() => {
    const set = new Set((metricsQuery.data ?? []).map((m) => m.category));
    return Array.from(set).sort();
  }, [metricsQuery.data]);

  const filtered = useMemo(() => {
    let rows = metricsQuery.data ?? [];
    if (category) rows = rows.filter((m) => m.category === category);
    if (search.trim()) {
      const needle = search.trim().toLowerCase();
      rows = rows.filter((m) => m.name.toLowerCase().includes(needle) || m.definition.toLowerCase().includes(needle));
    }
    return rows;
  }, [metricsQuery.data, category, search]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full max-w-sm">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search metrics…"
            className="pl-9"
            aria-label="Search metrics"
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Filter by category">
        <button
          type="button"
          role="tab"
          aria-selected={category === null}
          onClick={() => setCategory(null)}
          className={`rounded-full border px-3 py-1 text-xs font-medium capitalize transition-colors ${
            category === null
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border text-muted-foreground hover:bg-accent/60 hover:text-foreground"
          }`}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c}
            type="button"
            role="tab"
            aria-selected={category === c}
            onClick={() => setCategory(c)}
            className={`rounded-full border px-3 py-1 text-xs font-medium capitalize transition-colors ${
              category === c
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-muted-foreground hover:bg-accent/60 hover:text-foreground"
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {metricsQuery.isLoading ? (
        <LoadingState count={9} className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" itemClassName="h-32" />
      ) : metricsQuery.isError ? (
        <ErrorState
          title="Unable to load the metrics library"
          retry={() => void metricsQuery.refetch()}
        />
      ) : filtered.length === 0 ? (
        <EmptyState icon={BarChart3} title="No matching metrics" description="Try a different search or category." />
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((metric) => (
            <Card
              key={metric.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => setSelected(metric)}
            >
              <CardHeader>
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-foreground">{metric.name}</p>
                  <Badge variant="outline" className="shrink-0 capitalize">
                    {metric.category}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="line-clamp-3 text-sm text-muted-foreground">{metric.definition}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <MetricDetailSheet metric={selected} onOpenChange={(open) => !open && setSelected(null)} />
    </div>
  );
}
