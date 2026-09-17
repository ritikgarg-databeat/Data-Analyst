"use client";

import { useState } from "react";
import { AlertTriangle, Lightbulb } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useChart, useChartData, useUpdateChart } from "@/features/charts/use-charts";

import { PlotlyChartRenderer } from "./plotly-chart-renderer";

export function ChartViewer({ chartId }: { chartId: string }) {
  const chartQuery = useChart(chartId);
  const dataQuery = useChartData(chartId);
  const updateChart = useUpdateChart(chartId);

  const [showInsight, setShowInsight] = useState(false);
  const [observation, setObservation] = useState("");
  const [whyItMatters, setWhyItMatters] = useState("");
  const [recommendedAction, setRecommendedAction] = useState("");

  if (chartQuery.isLoading || dataQuery.isLoading) return <LoadingState count={1} itemClassName="h-96" />;
  if (chartQuery.isError || dataQuery.isError || !chartQuery.data || !dataQuery.data) {
    return <ErrorState title="Unable to load this chart" retry={() => void dataQuery.refetch()} />;
  }

  const chart = chartQuery.data;
  const data = dataQuery.data;

  function handleSaveInsight() {
    updateChart.mutate({
      insight_observation: observation.trim() || undefined,
      insight_why_it_matters: whyItMatters.trim() || undefined,
      insight_recommended_action: recommendedAction.trim() || undefined,
    });
    setShowInsight(false);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-xl border border-border bg-card p-3">
        <PlotlyChartRenderer
          chartType={chart.chart_type}
          data={data}
          title={chart.config.title ?? chart.title}
          xLabel={chart.config.x_label ?? undefined}
          yLabel={chart.config.y_label ?? undefined}
        />
      </div>

      {data.warnings.length > 0 ? (
        <div className="flex flex-col gap-1.5 rounded-lg border border-warning/40 bg-warning/10 p-3">
          {data.warnings.map((w, i) => (
            <p key={i} className="flex items-start gap-2 text-sm text-foreground">
              <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-warning" aria-hidden="true" />
              {w}
            </p>
          ))}
        </div>
      ) : null}

      {data.recommendation ? (
        <p className="rounded-md bg-accent/40 px-3 py-2 text-xs text-foreground">
          Suggestion: {data.recommendation}
        </p>
      ) : null}

      <div className="rounded-xl border border-border bg-card p-4">
        {chart.insight_observation && !showInsight ? (
          <div className="flex flex-col gap-1 text-sm">
            <p>
              <span className="font-semibold text-foreground">Observation: </span>
              {chart.insight_observation}
            </p>
            {chart.insight_why_it_matters ? (
              <p>
                <span className="font-semibold text-foreground">Why it matters: </span>
                {chart.insight_why_it_matters}
              </p>
            ) : null}
            {chart.insight_recommended_action ? (
              <p>
                <span className="font-semibold text-foreground">Recommended action: </span>
                {chart.insight_recommended_action}
              </p>
            ) : null}
            <Button variant="ghost" size="sm" className="mt-1 self-start" onClick={() => setShowInsight(true)}>
              Edit insight
            </Button>
          </div>
        ) : !showInsight ? (
          <Button variant="outline" size="sm" onClick={() => setShowInsight(true)}>
            <Lightbulb className="size-4" aria-hidden="true" />
            Add Insight
          </Button>
        ) : (
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium text-muted-foreground">Observation</label>
            <Input value={observation} onChange={(e) => setObservation(e.target.value)} />
            <label className="text-xs font-medium text-muted-foreground">Why it matters</label>
            <Textarea value={whyItMatters} onChange={(e) => setWhyItMatters(e.target.value)} className="min-h-16" />
            <label className="text-xs font-medium text-muted-foreground">Recommended action</label>
            <Textarea
              value={recommendedAction}
              onChange={(e) => setRecommendedAction(e.target.value)}
              className="min-h-16"
            />
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setShowInsight(false)}>
                Cancel
              </Button>
              <Button size="sm" onClick={handleSaveInsight}>
                Save
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
