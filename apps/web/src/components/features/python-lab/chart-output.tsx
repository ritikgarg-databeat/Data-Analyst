"use client";

import { useMemo } from "react";
import type { ChartOutputSchema } from "@data-analyst-lab/shared";
import type { Data, Layout } from "plotly.js";

import { PlotlyView } from "@/components/shared/plotly-view";
import { cn } from "@/lib/utils";

interface ChartOutputProps {
  chart: ChartOutputSchema;
  className?: string;
}

interface PlotlySpec {
  data: Data[];
  layout?: Partial<Layout>;
}

/** Renders one chart returned by a Python execution — a ready-to-display matplotlib PNG or a Plotly figure spec. */
export function ChartOutput({ chart, className }: ChartOutputProps) {
  if (chart.format === "plotly_json") {
    return <PlotlyChartOutput chart={chart} className={className} />;
  }

  return (
    <figure className={cn("overflow-hidden rounded-xl border border-border bg-card p-2", className)}>
      {/* eslint-disable-next-line @next/next/no-img-element -- data: URI rendered from an execution result, not a build-time-known asset */}
      <img
        src={`data:image/png;base64,${chart.data}`}
        alt={chart.title ?? "Matplotlib chart output"}
        className="mx-auto max-w-full"
      />
      {chart.title ? (
        <figcaption className="mt-1 text-center text-xs text-muted-foreground">{chart.title}</figcaption>
      ) : null}
    </figure>
  );
}

function PlotlyChartOutput({ chart, className }: ChartOutputProps) {
  const spec = useMemo<PlotlySpec | null>(() => {
    try {
      return JSON.parse(chart.data) as PlotlySpec;
    } catch {
      return null;
    }
  }, [chart.data]);

  if (!spec) {
    return (
      <p
        role="alert"
        className={cn(
          "rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive",
          className,
        )}
      >
        Couldn&apos;t parse this Plotly chart&apos;s spec.
      </p>
    );
  }

  return (
    <div className={cn("overflow-hidden rounded-xl border border-border bg-card p-2", className)}>
      <PlotlyView
        data={spec.data}
        layout={{ autosize: true, margin: { t: 32, r: 16, b: 32, l: 48 }, ...spec.layout }}
        style={{ width: "100%", height: "360px" }}
      />
      {chart.title ? <p className="mt-1 text-center text-xs text-muted-foreground">{chart.title}</p> : null}
    </div>
  );
}
