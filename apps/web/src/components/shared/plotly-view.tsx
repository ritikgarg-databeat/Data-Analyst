"use client";

import dynamic from "next/dynamic";

import type { PlotlyViewInnerProps } from "./plotly-view-inner";

// Plotly (and its WebGL/glslify dependency chain) must never be traced into
// the server bundle — `ssr: false` excludes plotly-view-inner.tsx's entire
// module graph from it. See that file's docstring for the full story.
const PlotlyViewInner = dynamic(() => import("./plotly-view-inner"), {
  ssr: false,
  loading: () => (
    <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">Loading chart…</div>
  ),
});

/** Shared Plotly renderer for any `{ data, layout }` spec — see plotly-view-inner.tsx for why this indirection exists. */
export function PlotlyView(props: PlotlyViewInnerProps) {
  return <PlotlyViewInner {...props} />;
}
