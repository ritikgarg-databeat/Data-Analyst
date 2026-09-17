"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import type { SchemaColumnSchema } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const DATA_TYPE_VARIANT: Record<string, "default" | "secondary" | "outline"> = {
  numeric: "default",
  categorical: "secondary",
  datetime: "outline",
  text: "outline",
  boolean: "secondary",
};

type SortKey = "column_name" | "data_type" | "null_percentage" | "unique_count";

function SortHeader({
  label,
  sortField,
  activeKey,
  desc,
  onToggle,
}: {
  label: string;
  sortField: SortKey;
  activeKey: SortKey;
  desc: boolean;
  onToggle: (key: SortKey) => void;
}) {
  const active = activeKey === sortField;
  return (
    <th scope="col" className="px-4 py-2 text-left">
      <button
        type="button"
        onClick={() => onToggle(sortField)}
        aria-label={`Sort by ${label}`}
        className="flex items-center gap-1 text-xs font-medium text-muted-foreground uppercase hover:text-foreground"
      >
        {label}
        {active ? (
          desc ? <ArrowDown className="size-3" /> : <ArrowUp className="size-3" />
        ) : (
          <ArrowUpDown className="size-3 opacity-40" />
        )}
      </button>
    </th>
  );
}

export function SchemaViewer({
  columns,
  onSelectColumn,
}: {
  columns: SchemaColumnSchema[];
  onSelectColumn: (column: SchemaColumnSchema) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("column_name");
  const [sortDesc, setSortDesc] = useState(false);

  const sorted = useMemo(() => {
    const copy = [...columns];
    copy.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      const cmp = typeof aVal === "number" && typeof bVal === "number" ? aVal - bVal : String(aVal).localeCompare(String(bVal));
      return sortDesc ? -cmp : cmp;
    });
    return copy;
  }, [columns, sortKey, sortDesc]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDesc((prev) => !prev);
    } else {
      setSortKey(key);
      setSortDesc(false);
    }
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-[560px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50">
            <SortHeader label="Column" sortField="column_name" activeKey={sortKey} desc={sortDesc} onToggle={toggleSort} />
            <SortHeader label="Type" sortField="data_type" activeKey={sortKey} desc={sortDesc} onToggle={toggleSort} />
            <SortHeader
              label="Nulls"
              sortField="null_percentage"
              activeKey={sortKey}
              desc={sortDesc}
              onToggle={toggleSort}
            />
            <SortHeader
              label="Unique"
              sortField="unique_count"
              activeKey={sortKey}
              desc={sortDesc}
              onToggle={toggleSort}
            />
          </tr>
        </thead>
        <tbody>
          {sorted.map((col) => (
            <tr
              key={col.column_name}
              className="cursor-pointer border-b border-border last:border-0 hover:bg-muted/30"
              onClick={() => onSelectColumn(col)}
            >
              <td className="px-4 py-2.5 font-medium text-foreground">
                {col.column_name}
                <span className="ml-2 text-xs font-normal text-muted-foreground">{col.inferred_sql_type}</span>
              </td>
              <td className="px-4 py-2.5">
                <Badge variant={DATA_TYPE_VARIANT[col.data_type] ?? "outline"}>{col.data_type}</Badge>
              </td>
              <td className="px-4 py-2.5">
                <span
                  className={cn(
                    "tabular-nums",
                    col.null_percentage >= 20 ? "font-medium text-destructive" : "text-muted-foreground",
                  )}
                >
                  {col.null_percentage.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-2.5 tabular-nums text-muted-foreground">
                {col.unique_count.toLocaleString()} ({col.unique_percentage.toFixed(1)}%)
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
