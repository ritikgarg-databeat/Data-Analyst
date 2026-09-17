"use client";

import { Handle, Position } from "@xyflow/react";
import { Key, Link2 } from "lucide-react";
import type { DataModelColumnSchema, DataModelTableType } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface TableNodeData {
  name: string;
  table_type: DataModelTableType;
  grain: string | null;
  notes: string | null;
  columns: DataModelColumnSchema[];
  [key: string]: unknown;
}

const TYPE_COLOR: Record<string, string> = {
  FACT: "border-l-primary",
  DIMENSION: "border-l-sky-500",
  BRIDGE: "border-l-violet-500",
  SOURCE: "border-l-muted-foreground",
  STORAGE: "border-l-amber-500",
  WAREHOUSE: "border-l-primary",
  TRANSFORM: "border-l-fuchsia-500",
  SERVICE: "border-l-sky-500",
  STREAM: "border-l-rose-500",
  BI: "border-l-emerald-500",
  OTHER: "border-l-border",
};

/** A table/node card — a real database table (Data Modeler), an architecture component,
 * or a pipeline stage, depending on the parent model's `model_kind`. */
export function TableNode({ data, selected }: { data: TableNodeData; selected?: boolean }) {
  return (
    <div
      className={cn(
        "w-56 rounded-lg border border-l-4 bg-card shadow-sm",
        TYPE_COLOR[data.table_type] ?? "border-l-border",
        selected ? "border-primary ring-2 ring-primary/30" : "border-border",
      )}
    >
      <Handle type="target" position={Position.Left} className="!bg-border" />
      <Handle type="source" position={Position.Right} className="!bg-border" />

      <div className="border-b border-border px-3 py-1.5">
        <p className="truncate text-sm font-semibold text-foreground">{data.name || "Untitled table"}</p>
        <div className="mt-0.5 flex items-center gap-1.5">
          <Badge variant="outline" className="text-[10px]">
            {data.table_type}
          </Badge>
          {data.grain ? <span className="truncate text-[10px] text-muted-foreground">{data.grain}</span> : null}
        </div>
      </div>

      {data.columns.length > 0 ? (
        <ul className="max-h-40 overflow-y-auto px-3 py-1.5 text-xs">
          {data.columns.map((col) => (
            <li key={col.name} className="flex items-center gap-1.5 py-0.5">
              {col.is_primary_key ? <Key className="size-3 shrink-0 text-amber-500" aria-hidden="true" /> : null}
              {col.is_foreign_key ? <Link2 className="size-3 shrink-0 text-sky-500" aria-hidden="true" /> : null}
              <span className="truncate font-mono text-foreground">{col.name}</span>
              {col.data_type ? (
                <span className="ml-auto shrink-0 text-[10px] text-muted-foreground">{col.data_type}</span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : (
        <p className="px-3 py-2 text-xs text-muted-foreground">No columns yet</p>
      )}
    </div>
  );
}
