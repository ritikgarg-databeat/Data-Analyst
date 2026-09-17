"use client";

import { RefreshCw } from "lucide-react";
import type { ServiceStatusLevel } from "@data-analyst-lab/shared";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useSystemHealth } from "@/features/platform/use-platform";
import { cn } from "@/lib/utils";

const STATUS_DOT: Record<ServiceStatusLevel, string> = {
  ok: "bg-success",
  degraded: "bg-warning",
  unavailable: "bg-destructive",
  not_configured: "bg-muted-foreground/40",
};

const STATUS_LABEL: Record<ServiceStatusLevel, string> = {
  ok: "OK",
  degraded: "Degraded",
  unavailable: "Unavailable",
  not_configured: "Not configured",
};

/**
 * System Health (Phase 12) — a live-status panel over GET /platform/health.
 * `not_configured` is expected/fine (optional integrations) and shown
 * neutrally in gray; `unavailable` is a real problem and shown in red.
 */
export function SystemHealthCard() {
  const { data, isLoading, isError, refetch, isFetching } = useSystemHealth();

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>System Health</CardTitle>
            <CardDescription>Live status of every backend service this platform depends on.</CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => void refetch()} disabled={isFetching}>
            <RefreshCw className={cn("size-3.5", isFetching && "animate-spin")} aria-hidden="true" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <LoadingState count={7} itemClassName="h-10" />
        ) : isError || !data ? (
          <ErrorState
            title="Unable to load system health"
            message="We couldn't reach the API to check system health."
            retry={() => void refetch()}
          />
        ) : (
          <ul className="flex flex-col divide-y divide-border">
            {data.services.map((service) => (
              <li key={service.name} className="flex items-center gap-3 py-2.5">
                <span
                  className={cn("size-2.5 shrink-0 rounded-full", STATUS_DOT[service.status])}
                  aria-hidden="true"
                />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-foreground">{service.name}</p>
                  {service.detail ? <p className="text-xs text-muted-foreground">{service.detail}</p> : null}
                </div>
                <span className="shrink-0 text-xs font-medium text-muted-foreground">
                  {STATUS_LABEL[service.status]}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
