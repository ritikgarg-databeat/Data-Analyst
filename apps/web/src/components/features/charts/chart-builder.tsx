"use client";

import { useState } from "react";
import { Sparkles } from "lucide-react";
import type { ChartConfig, SchemaColumnSchema } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useRecommendChart } from "@/features/charts/use-charts";

const CHART_TYPES = [
  { value: "bar", label: "Bar" },
  { value: "line", label: "Line" },
  { value: "scatter", label: "Scatter" },
  { value: "histogram", label: "Histogram" },
  { value: "box", label: "Box Plot" },
  { value: "heatmap", label: "Heatmap" },
  { value: "pie", label: "Pie" },
  { value: "donut", label: "Donut" },
];

const NEEDS_Y = new Set(["bar", "line", "scatter", "box", "heatmap", "pie", "donut"]);
const NEEDS_AGGREGATION = new Set(["bar", "line", "pie", "donut"]);
const NEEDS_BINS = new Set(["histogram"]);
const NEEDS_GRANULARITY = new Set(["line"]);
const NEEDS_SORT = new Set(["bar"]);
const SUPPORTS_COLOR = new Set(["bar", "line", "scatter"]);

export interface ChartDraft {
  chartType: string;
  title: string;
  config: ChartConfig;
}

interface ChartBuilderProps {
  columns: SchemaColumnSchema[];
  onCreate: (draft: ChartDraft) => void;
  isCreating: boolean;
}

function typeOf(columns: SchemaColumnSchema[], name: string): "numeric" | "categorical" | "datetime" {
  const col = columns.find((c) => c.column_name === name);
  if (!col) return "categorical";
  if (col.data_type === "numeric") return "numeric";
  if (col.data_type === "datetime") return "datetime";
  return "categorical";
}

/** The point-and-click Chart Builder (sections 23-25 of the Phase 5 spec). */
export function ChartBuilder({ columns, onCreate, isCreating }: ChartBuilderProps) {
  const [chartType, setChartType] = useState("bar");
  const [x, setX] = useState(columns[0]?.column_name ?? "");
  const [y, setY] = useState(columns.find((c) => c.data_type === "numeric")?.column_name ?? "");
  const [aggregation, setAggregation] = useState("SUM");
  const [color, setColor] = useState("");
  const [sort, setSort] = useState("");
  const [bins, setBins] = useState(20);
  const [granularity, setGranularity] = useState("month");
  const [title, setTitle] = useState("");
  const [xLabel, setXLabel] = useState("");
  const [yLabel, setYLabel] = useState("");

  const recommend = useRecommendChart();

  function handleRecommend() {
    const xType = typeOf(columns, x);
    const yType = NEEDS_Y.has(chartType) && y ? typeOf(columns, y) : undefined;
    recommend.mutate({ x_type: xType, y_type: yType });
  }

  function handleCreate() {
    const config: ChartConfig = {
      x: x || undefined,
      y: NEEDS_Y.has(chartType) ? y || undefined : undefined,
      aggregation: NEEDS_AGGREGATION.has(chartType) ? aggregation : undefined,
      color: SUPPORTS_COLOR.has(chartType) ? color || undefined : undefined,
      sort: NEEDS_SORT.has(chartType) && sort ? (sort as ChartConfig["sort"]) : undefined,
      bins: NEEDS_BINS.has(chartType) ? bins : undefined,
      date_granularity: NEEDS_GRANULARITY.has(chartType) ? (granularity as ChartConfig["date_granularity"]) : undefined,
      title: title || undefined,
      x_label: xLabel || undefined,
      y_label: yLabel || undefined,
    };
    onCreate({ chartType, title: title || `${chartType} chart`, config });
  }

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-4">
      <p className="text-sm font-semibold text-foreground">Chart Builder</p>

      <div className="flex flex-col gap-1">
        <Label htmlFor="chart-type">Chart Type</Label>
        <Select id="chart-type" value={chartType} onChange={(e) => setChartType(e.target.value)}>
          {CHART_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </Select>
      </div>

      <div className="flex flex-col gap-1">
        <Label htmlFor="chart-x">{chartType === "histogram" || chartType === "box" ? "Column" : "X Axis"}</Label>
        <Select id="chart-x" value={x} onChange={(e) => setX(e.target.value)}>
          {columns.map((c) => (
            <option key={c.column_name} value={c.column_name}>
              {c.column_name} ({c.data_type})
            </option>
          ))}
        </Select>
      </div>

      {NEEDS_Y.has(chartType) ? (
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-y">Y Axis</Label>
          <Select id="chart-y" value={y} onChange={(e) => setY(e.target.value)}>
            <option value="">— none (count) —</option>
            {columns.map((c) => (
              <option key={c.column_name} value={c.column_name}>
                {c.column_name} ({c.data_type})
              </option>
            ))}
          </Select>
        </div>
      ) : null}

      {NEEDS_AGGREGATION.has(chartType) ? (
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-agg">Aggregation</Label>
          <Select id="chart-agg" value={aggregation} onChange={(e) => setAggregation(e.target.value)}>
            {["SUM", "AVG", "COUNT", "MIN", "MAX"].map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </Select>
        </div>
      ) : null}

      {SUPPORTS_COLOR.has(chartType) ? (
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-color">Color</Label>
          <Select id="chart-color" value={color} onChange={(e) => setColor(e.target.value)}>
            <option value="">— none —</option>
            {columns.map((c) => (
              <option key={c.column_name} value={c.column_name}>
                {c.column_name}
              </option>
            ))}
          </Select>
        </div>
      ) : null}

      {NEEDS_SORT.has(chartType) ? (
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-sort">Sort</Label>
          <Select id="chart-sort" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="">Unsorted</option>
            <option value="y_desc">Value (high to low)</option>
            <option value="y_asc">Value (low to high)</option>
            <option value="x_asc">Category (A-Z)</option>
            <option value="x_desc">Category (Z-A)</option>
          </Select>
        </div>
      ) : null}

      {NEEDS_BINS.has(chartType) ? (
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-bins">Bins</Label>
          <Input
            id="chart-bins"
            type="number"
            min={2}
            max={100}
            value={bins}
            onChange={(e) => setBins(Number(e.target.value) || 20)}
          />
        </div>
      ) : null}

      {NEEDS_GRANULARITY.has(chartType) ? (
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-granularity">Granularity</Label>
          <Select id="chart-granularity" value={granularity} onChange={(e) => setGranularity(e.target.value)}>
            {["day", "week", "month", "quarter", "year"].map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </Select>
        </div>
      ) : null}

      <div className="flex flex-col gap-1">
        <Label htmlFor="chart-title">Title</Label>
        <Input id="chart-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Revenue by country" />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-xlabel">X Label</Label>
          <Input id="chart-xlabel" value={xLabel} onChange={(e) => setXLabel(e.target.value)} />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="chart-ylabel">Y Label</Label>
          <Input id="chart-ylabel" value={yLabel} onChange={(e) => setYLabel(e.target.value)} />
        </div>
      </div>

      <Button variant="ghost" size="sm" className="self-start" onClick={handleRecommend} disabled={recommend.isPending}>
        <Sparkles className="size-4" aria-hidden="true" />
        What chart should I use?
      </Button>
      {recommend.data ? (
        <p className="rounded-md bg-accent/40 px-3 py-2 text-xs text-foreground">
          Recommended: <strong>{recommend.data.chart_type}</strong> — {recommend.data.reason}
        </p>
      ) : null}

      <Button onClick={handleCreate} disabled={!x || isCreating} className="mt-1">
        {isCreating ? "Creating…" : "Create Chart"}
      </Button>
    </div>
  );
}
