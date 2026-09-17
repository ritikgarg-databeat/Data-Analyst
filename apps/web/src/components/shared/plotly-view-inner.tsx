"use client";

import { useEffect, useRef } from "react";
// The full `plotly.js` package entry point pulls in every trace family
// (3D/WebGL/geo/maps) and, with it, several Node-oriented transitive deps
// (`buffer/`, dynamic `require()`s inside `glslify`) that Turbopack can't
// resolve for the browser bundle at all. `dist/plotly-cartesian` is
// Plotly's own pre-bundled, browser-ready build covering exactly the 2D
// chart families this app renders (bar/line/scatter/histogram/box/heatmap/
// pie) — already bundled, so nothing left for Turbopack to resolve.
import Plotly from "plotly.js/dist/plotly-cartesian";
import type { Data, Layout } from "plotly.js";

export interface PlotlyViewInnerProps {
  data: Data[];
  layout: Partial<Layout>;
  style?: React.CSSProperties;
  emptyMessage?: string;
}

/**
 * Drives the `plotly.js` API directly (`Plotly.newPlot`/`purge`/`Plots.resize`
 * in a plain `useEffect`) instead of the `react-plotly.js` wrapper — that
 * wrapper mounts its `.js-plotly-plot` container but never actually calls
 * into Plotly under this app's React 19 setup (confirmed live: `window.Plotly`
 * loaded and worked fine when invoked manually; react-plotly.js's own effect
 * just never fired it — a latent incompatibility, not a Plotly bug).
 *
 * This file has a *static* top-level `import Plotly from "plotly.js/dist/
 * plotly-cartesian"` — safe ONLY because `plotly-view.tsx` loads this whole
 * module via `next/dynamic(..., { ssr: false })`, which excludes this
 * file's entire module graph (Plotly and its WebGL/glslify dependency
 * chain) from the server bundle. Never import this file directly from
 * server-rendered code, and never turn the Plotly import into a bare
 * dynamic `import()` inside a plain component — Turbopack still traces
 * *those* for the SSR bundle and fails resolving `glslify`'s dynamic
 * `require()`.
 *
 * React (in dev, under StrictMode) mounts every effect, cleans it up, then
 * mounts it again immediately. `newPlot` is async, so naively firing a
 * second `newPlot` call before the first has resolved runs TWO concurrent
 * `newPlot` calls against the *same* DOM node — Plotly isn't built to
 * survive that (the div stays tagged `.js-plotly-plot` but never gets an
 * SVG child, permanently, no matter how the two results are reconciled
 * afterward — the concurrency itself is the bug). The fix is strict
 * sequencing: every newPlot/purge call for this component instance is
 * chained onto one shared promise, so a remount's newPlot can only ever
 * start after the previous mount's newPlot *and* its cleanup's purge have
 * both fully finished.
 */
export default function PlotlyViewInner({ data, layout, style, emptyMessage }: PlotlyViewInnerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pendingRef = useRef<Promise<unknown>>(Promise.resolve());

  useEffect(() => {
    const container = containerRef.current;
    if (!container || data.length === 0) return;

    let live = true;
    pendingRef.current = pendingRef.current.catch(() => {}).then(() => {
      if (!live) return undefined;
      return Plotly.newPlot(container, data, layout, { displaylogo: false, responsive: true });
    });

    // See the module docstring: `container` is guaranteed non-null in both
    // closures below (we returned early above otherwise) — TypeScript's
    // narrowing just doesn't follow a `const` into nested closures this deep.
    function handleResize() {
      if (live) Plotly.Plots.resize(container!);
    }
    window.addEventListener("resize", handleResize);

    return () => {
      live = false;
      window.removeEventListener("resize", handleResize);
      pendingRef.current = pendingRef.current.catch(() => {}).then(() => {
        Plotly.purge(container!);
      });
    };
  }, [data, layout]);

  if (data.length === 0) {
    return (
      <p className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        {emptyMessage ?? "No chart data."}
      </p>
    );
  }

  return <div ref={containerRef} style={style ?? { width: "100%", height: "360px" }} />;
}
