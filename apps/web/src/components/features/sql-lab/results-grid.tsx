"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown, Check, Copy, Download, TableIcon } from "lucide-react";
import type { SqlColumnInfo } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 50;

type SortDirection = "asc" | "desc";

interface SortState {
  columnIndex: number;
  direction: SortDirection;
}

interface ResultsGridProps {
  columns: SqlColumnInfo[];
  rows: unknown[][];
  /** Total rows the query/table actually has (may be larger than `rows.length` when truncated). */
  rowCount: number;
  /** True when the backend capped the returned rows below the query's real match count. */
  truncated?: boolean;
  className?: string;
  pageSize?: number;
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function compareValues(a: unknown, b: unknown): number {
  const aNull = a === null || a === undefined;
  const bNull = b === null || b === undefined;
  if (aNull && bNull) return 0;
  if (aNull) return 1; // nulls sort last regardless of direction
  if (bNull) return -1;

  if (typeof a === "number" && typeof b === "number") return a - b;

  const aNum = typeof a === "string" && a.trim() !== "" ? Number(a) : NaN;
  const bNum = typeof b === "string" && b.trim() !== "" ? Number(b) : NaN;
  if (!Number.isNaN(aNum) && !Number.isNaN(bNum)) return aNum - bNum;

  return String(a).localeCompare(String(b));
}

function toDelimitedText(columns: SqlColumnInfo[], rows: unknown[][], delimiter: string): string {
  const escape = (raw: string) => {
    if (delimiter === "," && /[",\n]/.test(raw)) {
      return `"${raw.replace(/"/g, '""')}"`;
    }
    return raw;
  };
  const header = columns.map((c) => escape(c.name)).join(delimiter);
  const body = rows.map((row) => row.map((cell) => escape(formatCell(cell))).join(delimiter)).join("\n");
  return `${header}\n${body}`;
}

function downloadCsv(columns: SqlColumnInfo[], rows: unknown[][], filename: string) {
  const csv = toDelimitedText(columns, rows, ",");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Reusable, sortable/paginated tabular results viewer for anything shaped
 * like `{ columns, rows }` — SQL Lab execution results and table previews
 * both render through this one component.
 */
export function ResultsGrid({ columns, rows, rowCount, truncated = false, className, pageSize = PAGE_SIZE }: ResultsGridProps) {
  const [sort, setSort] = useState<SortState | null>(null);
  const [page, setPage] = useState(0);
  const [copied, setCopied] = useState(false);

  const sortedRows = useMemo(() => {
    if (!sort) return rows;
    const { columnIndex, direction } = sort;
    const copy = [...rows];
    copy.sort((a, b) => {
      const result = compareValues(a[columnIndex], b[columnIndex]);
      return direction === "asc" ? result : -result;
    });
    return copy;
  }, [rows, sort]);

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / pageSize));
  const clampedPage = Math.min(page, totalPages - 1);
  const pageRows = useMemo(
    () => sortedRows.slice(clampedPage * pageSize, clampedPage * pageSize + pageSize),
    [sortedRows, clampedPage, pageSize],
  );

  function handleSort(columnIndex: number) {
    setPage(0);
    setSort((prev) => {
      if (!prev || prev.columnIndex !== columnIndex) return { columnIndex, direction: "asc" };
      if (prev.direction === "asc") return { columnIndex, direction: "desc" };
      return null;
    });
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(toDelimitedText(columns, sortedRows, "\t"));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API unavailable (e.g. insecure context) — silently ignore, the export button still works.
    }
  }

  if (columns.length === 0 && rows.length === 0) {
    return (
      <EmptyState
        icon={TableIcon}
        title="No results yet"
        description="Run a query to see its output here."
        className={className}
      />
    );
  }

  if (rows.length === 0) {
    return (
      <div className={cn("space-y-3", className)}>
        <EmptyState
          icon={TableIcon}
          title="No rows returned"
          description="Your query ran successfully but didn't match any rows."
        />
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">
          {rowCount.toLocaleString()} row{rowCount === 1 ? "" : "s"}
          {columns.length > 0 ? ` · ${columns.length} column${columns.length === 1 ? "" : "s"}` : ""}
        </p>
        <div className="flex items-center gap-1.5">
          <Button type="button" size="sm" variant="outline" onClick={() => void handleCopy()}>
            {copied ? <Check className="size-3.5" aria-hidden="true" /> : <Copy className="size-3.5" aria-hidden="true" />}
            {copied ? "Copied" : "Copy"}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => downloadCsv(columns, sortedRows, "query-results.csv")}
          >
            <Download className="size-3.5" aria-hidden="true" />
            Export CSV
          </Button>
        </div>
      </div>

      {truncated ? (
        <p className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-xs text-warning-foreground">
          Results truncated at {rowCount.toLocaleString()} row{rowCount === 1 ? "" : "s"} — this query matched more
          rows than SQL Lab&apos;s per-query cap allows. Add a <code className="font-mono">LIMIT</code> or narrow your
          filters to see a different slice.
        </p>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-border">
        <table className="w-full min-w-max border-collapse text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 text-left text-xs font-medium text-muted-foreground uppercase">
              {columns.map((column, index) => {
                const isSorted = sort?.columnIndex === index;
                const Icon = isSorted ? (sort?.direction === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
                return (
                  <th key={column.name + index} scope="col" className="px-4 py-2.5 whitespace-nowrap">
                    <button
                      type="button"
                      onClick={() => handleSort(index)}
                      className={cn(
                        "flex items-center gap-1 outline-none hover:text-foreground focus-visible:text-foreground",
                        isSorted && "text-foreground",
                      )}
                    >
                      {column.name}
                      <Icon className="size-3" aria-hidden="true" />
                      <span className="sr-only">Sort by {column.name}</span>
                    </button>
                    <span className="block text-[10px] font-normal normal-case text-muted-foreground/70">
                      {column.type}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, rowIndex) => (
              <tr key={clampedPage * pageSize + rowIndex} className="border-b border-border last:border-0 hover:bg-muted/30">
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
  );
}
