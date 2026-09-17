"use client";

import { useMemo, useState } from "react";
import { Database, Download } from "lucide-react";
import type { DataFrameSummarySchema } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 25;

type DataFrameTab = "preview" | "schema" | "stats";

const TABS: { key: DataFrameTab; label: string }[] = [
  { key: "preview", label: "Preview" },
  { key: "schema", label: "Schema" },
  { key: "stats", label: "Statistics" },
];

interface DataFrameViewerProps {
  dataframe: DataFrameSummarySchema;
  /** Shown in a small caption near the header, e.g. the variable's name — purely cosmetic. */
  name?: string;
  className?: string;
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/** Formats a byte count as a human-readable size, e.g. 2 516 582 -> "2.4 MB". */
export function formatBytes(bytes: number | null): string {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`;
}

function downloadBlob(content: string, mimeType: string, filename: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function toCsv(dataframe: DataFrameSummarySchema): string {
  const escape = (raw: string) => (/[",\n]/.test(raw) ? `"${raw.replace(/"/g, '""')}"` : raw);
  const header = dataframe.columns.map((c) => escape(c.name)).join(",");
  const body = dataframe.preview_rows.map((row) => row.map((cell) => escape(formatCell(cell))).join(",")).join("\n");
  return `${header}\n${body}`;
}

function toJson(dataframe: DataFrameSummarySchema): string {
  const records = dataframe.preview_rows.map((row) =>
    Object.fromEntries(dataframe.columns.map((column, index) => [column.name, row[index]])),
  );
  return JSON.stringify(records, null, 2);
}

/**
 * The "DataFrame Viewer": row/column counts, a paginated raw-values preview,
 * a schema (name/dtype) table, and per-column missing/unique statistics plus
 * memory usage. Given a `DataFrameSummarySchema` from a Python execution
 * result — never re-fetches anything itself.
 */
export function DataFrameViewer({ dataframe, name, className }: DataFrameViewerProps) {
  const [tab, setTab] = useState<DataFrameTab>("preview");
  const [page, setPage] = useState(0);

  const totalPages = Math.max(1, Math.ceil(dataframe.preview_rows.length / PAGE_SIZE));
  const clampedPage = Math.min(page, totalPages - 1);
  const pageRows = useMemo(
    () => dataframe.preview_rows.slice(clampedPage * PAGE_SIZE, clampedPage * PAGE_SIZE + PAGE_SIZE),
    [dataframe.preview_rows, clampedPage],
  );

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {name ? <span className="font-mono font-semibold text-foreground">{name}</span> : null}
          <span>
            {dataframe.row_count.toLocaleString()} row{dataframe.row_count === 1 ? "" : "s"} ×{" "}
            {dataframe.column_count} column{dataframe.column_count === 1 ? "" : "s"}
          </span>
          {dataframe.memory_usage_bytes != null ? <span>· {formatBytes(dataframe.memory_usage_bytes)}</span> : null}
        </div>
        <div className="flex items-center gap-1.5" title="Exports only the previewed rows shown here, not the full DataFrame.">
          <Button type="button" size="sm" variant="outline" onClick={() => downloadBlob(toCsv(dataframe), "text/csv;charset=utf-8;", "dataframe-preview.csv")}>
            <Download className="size-3.5" aria-hidden="true" />
            Export CSV
          </Button>
          <Button type="button" size="sm" variant="outline" onClick={() => downloadBlob(toJson(dataframe), "application/json;charset=utf-8;", "dataframe-preview.json")}>
            <Download className="size-3.5" aria-hidden="true" />
            Export JSON
          </Button>
        </div>
      </div>

      <div role="tablist" className="flex border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "border-b-2 px-3 py-1.5 text-xs font-medium transition-colors",
              tab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">
        {tab === "preview" ? (
          dataframe.preview_rows.length === 0 ? (
            <EmptyState icon={Database} title="No preview rows" description="This DataFrame has no rows to preview." />
          ) : (
            <div className="space-y-2">
              {dataframe.truncated ? (
                <p className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning-foreground">
                  Showing a preview of {dataframe.preview_row_count.toLocaleString()} row
                  {dataframe.preview_row_count === 1 ? "" : "s"} out of {dataframe.row_count.toLocaleString()} total —
                  the full DataFrame is larger than the preview cap.
                </p>
              ) : null}
              <div className="overflow-x-auto rounded-xl border border-border">
                <table className="w-full min-w-max border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
                      {dataframe.columns.map((column) => (
                        <th key={column.name} scope="col" className="px-4 py-2.5 whitespace-nowrap">
                          {column.name}
                          <span className="block text-[10px] font-normal normal-case text-muted-foreground/70">
                            {column.dtype}
                          </span>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map((row, rowIndex) => (
                      <tr
                        key={clampedPage * PAGE_SIZE + rowIndex}
                        className="border-b border-border last:border-0 hover:bg-muted/30"
                      >
                        {row.map((cell, cellIndex) => (
                          <td
                            key={cellIndex}
                            className={cn(
                              "px-4 py-2 whitespace-nowrap text-foreground",
                              (cell === null || cell === undefined) && "text-muted-foreground italic",
                            )}
                          >
                            {formatCell(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 ? (
                <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>
                    Page {clampedPage + 1} of {totalPages}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={clampedPage === 0}
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={clampedPage >= totalPages - 1}
                      onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              ) : null}
            </div>
          )
        ) : null}

        {tab === "schema" ? (
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-max border-collapse text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
                  <th scope="col" className="px-4 py-2.5">
                    Column
                  </th>
                  <th scope="col" className="px-4 py-2.5">
                    Dtype
                  </th>
                </tr>
              </thead>
              <tbody>
                {dataframe.columns.map((column) => (
                  <tr key={column.name} className="border-b border-border last:border-0">
                    <td className="px-4 py-2 font-mono text-foreground">{column.name}</td>
                    <td className="px-4 py-2 text-muted-foreground">{column.dtype}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {tab === "stats" ? (
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full min-w-max border-collapse text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
                  <th scope="col" className="px-4 py-2.5">
                    Column
                  </th>
                  <th scope="col" className="px-4 py-2.5 text-right">
                    Missing
                  </th>
                  <th scope="col" className="px-4 py-2.5 text-right">
                    Unique
                  </th>
                </tr>
              </thead>
              <tbody>
                {dataframe.columns.map((column) => (
                  <tr key={column.name} className="border-b border-border last:border-0">
                    <td className="px-4 py-2 font-mono text-foreground">{column.name}</td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">
                      {column.null_count.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right tabular-nums text-muted-foreground">
                      {column.unique_count.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
              Memory usage: {formatBytes(dataframe.memory_usage_bytes)}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}
