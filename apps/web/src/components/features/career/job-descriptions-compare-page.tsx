"use client";

import { useState } from "react";
import { GitCompare } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { useCompareJobDescriptions, useJobDescriptions } from "@/features/career/use-jobs";

export function JobDescriptionsComparePage() {
  const jobDescriptionsQuery = useJobDescriptions();
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const compareQuery = useCompareJobDescriptions(selectedIds);

  if (jobDescriptionsQuery.isLoading) return <LoadingState count={3} itemClassName="h-16" />;
  if (jobDescriptionsQuery.isError) {
    return (
      <ErrorState
        message="We couldn't reach the API to load your saved job descriptions."
        retry={() => void jobDescriptionsQuery.refetch()}
      />
    );
  }

  const jobDescriptions = jobDescriptionsQuery.data ?? [];

  function toggle(id: string) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Select 2 or More Job Descriptions</CardTitle>
        </CardHeader>
        <CardContent>
          {jobDescriptions.length === 0 ? (
            <EmptyState icon={GitCompare} title="No saved job descriptions" description="Save at least two job descriptions to compare them." />
          ) : (
            <ul className="flex flex-col gap-2">
              {jobDescriptions.map((jd) => (
                <li key={jd.id}>
                  <label className="flex items-center gap-2 text-sm">
                    <input type="checkbox" checked={selectedIds.includes(jd.id)} onChange={() => toggle(jd.id)} />
                    <span className="text-foreground">{jd.title}</span>
                    {jd.company ? <span className="text-muted-foreground">· {jd.company}</span> : null}
                  </label>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {selectedIds.length < 2 ? (
        <p className="text-sm text-muted-foreground">Pick at least two job descriptions above to see a comparison.</p>
      ) : compareQuery.isLoading ? (
        <LoadingState count={2} itemClassName="h-24" />
      ) : compareQuery.isError || !compareQuery.data ? (
        <ErrorState message="We couldn't compare these job descriptions." retry={() => void compareQuery.refetch()} />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Comparison</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full min-w-max border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
                    <th className="px-4 py-2.5">Title</th>
                    <th className="px-4 py-2.5">Company</th>
                    <th className="px-4 py-2.5">Readiness</th>
                    <th className="px-4 py-2.5">Must-Have Gaps</th>
                  </tr>
                </thead>
                <tbody>
                  {compareQuery.data.entries.map((entry) => (
                    <tr key={entry.job_description_id} className="border-b border-border last:border-0">
                      <td className="px-4 py-2 text-foreground">{entry.title}</td>
                      <td className="px-4 py-2 text-muted-foreground">{entry.company ?? "—"}</td>
                      <td className="px-4 py-2 text-foreground">
                        {entry.readiness_score != null ? `${entry.readiness_score.toFixed(0)}%` : "Not analyzed"}
                      </td>
                      <td className="px-4 py-2 text-muted-foreground">{entry.must_have_gap_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <p className="mb-1.5 text-sm font-medium text-foreground">Common must-have skills across all selected postings</p>
              {compareQuery.data.common_must_have_skill_slugs.length === 0 ? (
                <p className="text-sm text-muted-foreground">No must-have skill is shared by every selected posting.</p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {compareQuery.data.common_must_have_skill_slugs.map((slug) => (
                    <Badge key={slug} variant="outline">{slug}</Badge>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
