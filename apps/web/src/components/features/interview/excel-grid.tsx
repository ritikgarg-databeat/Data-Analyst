"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ExcelCellValue, ExcelSheet } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useEvaluateWorkbook } from "@/features/interview/use-interview";

const MIN_COLS = 8;
const MIN_ROWS = 15;
const EXTRA_COLS = 2;
const EXTRA_ROWS = 3;

function colLetter(index: number): string {
  let n = index + 1;
  let out = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    out = String.fromCharCode(65 + rem) + out;
    n = Math.floor((n - 1) / 26);
  }
  return out;
}

function parseRef(ref: string): { col: number; row: number } | null {
  const match = /^([A-Za-z]+)([0-9]+)$/.exec(ref);
  if (!match) return null;
  const [, letters, digits] = match;
  let col = 0;
  for (const ch of letters.toUpperCase()) col = col * 26 + (ch.charCodeAt(0) - 64);
  return { col: col - 1, row: parseInt(digits, 10) - 1 };
}

function gridDims(cells: Record<string, string>): { cols: number; rows: number } {
  let maxCol = MIN_COLS - 1;
  let maxRow = MIN_ROWS - 1;
  for (const ref of Object.keys(cells)) {
    const parsed = parseRef(ref);
    if (!parsed) continue;
    maxCol = Math.max(maxCol, parsed.col);
    maxRow = Math.max(maxRow, parsed.row);
  }
  return { cols: maxCol + 1 + EXTRA_COLS, rows: maxRow + 1 + EXTRA_ROWS };
}

function formatValue(value: ExcelCellValue | undefined): string {
  if (value === undefined || value === null) return "";
  if (typeof value === "boolean") return value ? "TRUE" : "FALSE";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/\.?0+$/, "");
  return value;
}

interface ExcelGridProps {
  sheets: ExcelSheet[];
  onChange: (sheets: ExcelSheet[]) => void;
  readOnly?: boolean;
  checkCells?: string[];
}

/** A real, lightweight spreadsheet grid (spec section 13) — cells/formulas/
 * multiple sheets/live recompute via the real formula engine, deliberately
 * NOT a full Excel clone (no fill-down, no cell formatting, no charts). */
export function ExcelGrid({ sheets, onChange, readOnly = false, checkCells = [] }: ExcelGridProps) {
  const [activeSheetIndex, setActiveSheetIndex] = useState(0);
  const [editingRef, setEditingRef] = useState<string | null>(null);
  const [draftValue, setDraftValue] = useState("");
  const evaluateWorkbook = useEvaluateWorkbook();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const activeSheet = sheets[activeSheetIndex] ?? sheets[0];
  const { cols, rows } = useMemo(() => gridDims(activeSheet?.cells ?? {}), [activeSheet]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      evaluateWorkbook.mutate(sheets);
    }, 400);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(sheets)]);

  const evaluatedSheet = evaluateWorkbook.data?.sheets.find((s) => s.name === activeSheet?.name);
  const checkCellSet = useMemo(() => new Set(checkCells.map((c) => c.split("!").pop() ?? c)), [checkCells]);

  function commitEdit(ref: string, rawValue: string) {
    const nextSheets = sheets.map((sheet, index) => {
      if (index !== activeSheetIndex) return sheet;
      const nextCells = { ...sheet.cells };
      if (rawValue.trim() === "") delete nextCells[ref];
      else nextCells[ref] = rawValue;
      return { ...sheet, cells: nextCells };
    });
    onChange(nextSheets);
  }

  return (
    <div className="flex flex-col gap-2 overflow-hidden rounded-xl border border-border bg-card">
      <div className="flex items-center gap-1 border-b border-border bg-muted/40 px-2 py-1.5">
        {sheets.map((sheet, index) => (
          <button
            key={sheet.name}
            type="button"
            onClick={() => setActiveSheetIndex(index)}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
              index === activeSheetIndex ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {sheet.name}
          </button>
        ))}
      </div>
      <div className="max-h-[420px] overflow-auto">
        <table className="w-full border-collapse text-xs">
          <thead className="sticky top-0 z-10 bg-muted/60">
            <tr>
              <th className="w-10 border border-border bg-muted/60 p-1" />
              {Array.from({ length: cols }, (_, c) => (
                <th key={c} className="min-w-20 border border-border p-1 font-medium text-muted-foreground">
                  {colLetter(c)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }, (_, r) => (
              <tr key={r}>
                <td className="border border-border bg-muted/40 p-1 text-center font-medium text-muted-foreground">{r + 1}</td>
                {Array.from({ length: cols }, (_, c) => {
                  const ref = `${colLetter(c)}${r + 1}`;
                  const isEditing = editingRef === ref;
                  const rawValue = activeSheet?.cells[ref] ?? "";
                  const evaluatedValue = evaluatedSheet?.cells[ref];
                  const isError = typeof evaluatedValue === "string" && evaluatedValue.startsWith("#");
                  const isCheckCell = checkCellSet.has(ref);
                  return (
                    <td
                      key={ref}
                      className={cn(
                        "border border-border p-0",
                        isCheckCell && !readOnly && "bg-primary/5",
                      )}
                    >
                      {isEditing && !readOnly ? (
                        <input
                          autoFocus
                          value={draftValue}
                          onChange={(e) => setDraftValue(e.target.value)}
                          onBlur={() => {
                            commitEdit(ref, draftValue);
                            setEditingRef(null);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === "Tab") {
                              commitEdit(ref, draftValue);
                              setEditingRef(null);
                            } else if (e.key === "Escape") {
                              setEditingRef(null);
                            }
                          }}
                          className="w-full min-w-20 border-none bg-background px-1.5 py-1 font-mono text-xs outline-none ring-1 ring-primary"
                          aria-label={`Cell ${ref} formula`}
                        />
                      ) : (
                        <button
                          type="button"
                          disabled={readOnly}
                          onClick={() => {
                            setEditingRef(ref);
                            setDraftValue(rawValue);
                          }}
                          className={cn(
                            "block w-full min-w-20 truncate px-1.5 py-1 text-left tabular-nums",
                            isError && "text-rose-600 dark:text-rose-400",
                            !rawValue && "text-muted-foreground/40",
                          )}
                          title={rawValue || undefined}
                        >
                          {formatValue(evaluatedValue) || (rawValue ? rawValue : "")}
                        </button>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!readOnly ? (
        <div className="flex items-center justify-between px-3 pb-2 text-xs text-muted-foreground">
          <span>Click a cell to enter a value or formula (start with =). Values recompute automatically.</span>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => evaluateWorkbook.mutate(sheets)}
            disabled={evaluateWorkbook.isPending}
          >
            Recalculate
          </Button>
        </div>
      ) : null}
    </div>
  );
}
