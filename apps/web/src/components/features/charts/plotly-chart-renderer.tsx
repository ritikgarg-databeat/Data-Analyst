"use client";

import { useMemo } from "react";
import type { ChartDataResponse } from "@data-analyst-lab/shared";
import type { Data, Layout } from "plotly.js";

import { PlotlyView } from "@/components/shared/plotly-view";

interface PlotlyChartRendererProps {
  chartType: string;
  data: ChartDataResponse;
  title?: string;
  xLabel?: string;
  yLabel?: string;
}

function buildTraces(chartType: string, data: ChartDataResponse): Data[] {
  const { x_values, series } = data;

  switch (chartType) {
    case "bar":
      return series.map((s) => ({ type: "bar", name: s.name, x: x_values, y: s.y_values }) as Data);
    case "line":
      return series.map(
        (s) => ({ type: "scatter", mode: "lines+markers", name: s.name, x: x_values, y: s.y_values }) as Data,
      );
    case "scatter":
      return series.map(
        (s) =>
          ({
            type: "scatter",
            mode: "markers",
            name: s.name,
            x: x_values,
            y: s.y_values,
            marker: s.color_values ? { color: s.color_values as number[], showscale: true } : undefined,
          }) as Data,
      );
    case "histogram":
      return [{ type: "bar", name: series[0]?.name ?? "count", x: x_values, y: series[0]?.y_values ?? [] } as Data];
    case "box":
      return [{ type: "box", name: series[0]?.name ?? "value", x: x_values, y: series[0]?.y_values ?? [] } as Data];
    case "heatmap":
      return [
        {
          type: "heatmap",
          x: x_values,
          y: series.map((s) => s.name),
          z: series.map((s) => s.y_values),
          colorscale: "Blues",
        } as Data,
      ];
    case "pie":
    case "donut":
      return [
        {
          type: "pie",
          labels: x_values,
          values: series[0]?.y_values ?? [],
          hole: chartType === "donut" ? 0.5 : 0,
        } as Data,
      ];
    default:
      return [];
  }
}

export function PlotlyChartRenderer({ chartType, data, title, xLabel, yLabel }: PlotlyChartRendererProps) {
  const traces = useMemo(() => buildTraces(chartType, data), [chartType, data]);
  const layout = useMemo<Partial<Layout>>(() => {
    // Plotly's own layout-cleaning code assumes an axis/title key, if
    // present at all, has a real value — an explicit `xaxis: undefined`
    // (as opposed to omitting the key) crashes deep inside `newPlot`
    // ("Cannot read properties of undefined (reading 'anchor')"). Build the
    // object with spreads instead of `key: cond ? value : undefined` so
    // unused keys are never added at all.
    return {
      autosize: true,
      margin: { t: title ? 40 : 16, r: 16, b: 48, l: 56 },
      showlegend: data.series.length > 1,
      ...(title ? { title: { text: title } } : {}),
      ...(xLabel ? { xaxis: { title: { text: xLabel } } } : {}),
      ...(yLabel ? { yaxis: { title: { text: yLabel } } } : {}),
    };
  }, [title, xLabel, yLabel, data.series.length]);

  return (
    <PlotlyView
      data={traces}
      layout={layout}
      style={{ width: "100%", height: "380px" }}
      emptyMessage="Choose axes to preview this chart."
    />
  );
}
