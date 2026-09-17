"use client";

import { Plus, Trash2 } from "lucide-react";
import type { DataModelColumnSchema, DataModelKind, DataModelTableType } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";

import type { TableNodeData } from "./table-node";

const TABLE_TYPES_BY_KIND: Record<DataModelKind, DataModelTableType[]> = {
  DIMENSIONAL: ["FACT", "DIMENSION", "BRIDGE", "OTHER"],
  ARCHITECTURE: ["SOURCE", "STORAGE", "WAREHOUSE", "TRANSFORM", "SERVICE", "STREAM", "BI", "OTHER"],
  PIPELINE: ["SOURCE", "STORAGE", "WAREHOUSE", "TRANSFORM", "SERVICE", "BI", "OTHER"],
};

interface TableEditorSheetProps {
  modelKind: DataModelKind;
  open: boolean;
  data: TableNodeData | null;
  otherTableNames: string[];
  onChange: (next: TableNodeData) => void;
  onDelete: () => void;
  onOpenChange: (open: boolean) => void;
}

function emptyColumn(): DataModelColumnSchema {
  return { name: "", is_primary_key: false, is_foreign_key: false };
}

export function TableEditorSheet({
  modelKind,
  open,
  data,
  otherTableNames,
  onChange,
  onDelete,
  onOpenChange,
}: TableEditorSheetProps) {
  if (!data) return null;

  function set<K extends keyof TableNodeData>(key: K, value: TableNodeData[K]) {
    onChange({ ...data!, [key]: value });
  }

  function setColumn(index: number, next: Partial<DataModelColumnSchema>) {
    const columns = [...data!.columns];
    columns[index] = { ...columns[index], ...next };
    set("columns", columns);
  }

  function addColumn() {
    set("columns", [...data!.columns, emptyColumn()]);
  }

  function removeColumn(index: number) {
    set(
      "columns",
      data!.columns.filter((_, i) => i !== index),
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full max-w-[26rem]">
        <SheetHeader>
          <SheetTitle>Edit table</SheetTitle>
        </SheetHeader>
        <div className="flex-1 space-y-4 overflow-y-auto px-4 pb-4">
          <div className="space-y-1">
            <Label htmlFor="table-name">Name</Label>
            <Input id="table-name" value={data.name} onChange={(e) => set("name", e.target.value)} />
          </div>

          <div className="space-y-1">
            <Label htmlFor="table-type">Type</Label>
            <Select
              id="table-type"
              value={data.table_type}
              onChange={(e) => set("table_type", e.target.value as DataModelTableType)}
            >
              {TABLE_TYPES_BY_KIND[modelKind].map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>
          </div>

          {modelKind === "DIMENSIONAL" ? (
            <div className="space-y-1">
              <Label htmlFor="table-grain">Grain</Label>
              <Input
                id="table-grain"
                value={data.grain ?? ""}
                onChange={(e) => set("grain", e.target.value || null)}
                placeholder='e.g. "1 row = 1 order"'
              />
            </div>
          ) : null}

          <div className="space-y-1">
            <Label htmlFor="table-notes">Notes</Label>
            <Textarea
              id="table-notes"
              value={data.notes ?? ""}
              onChange={(e) => set("notes", e.target.value || null)}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Columns</Label>
              <Button variant="ghost" size="sm" onClick={addColumn}>
                <Plus className="size-3.5" aria-hidden="true" />
                Add column
              </Button>
            </div>
            <div className="space-y-3">
              {data.columns.map((col, index) => (
                <div key={index} className="space-y-1.5 rounded-md border border-border p-2">
                  <div className="flex items-center gap-1.5">
                    <Input
                      value={col.name}
                      onChange={(e) => setColumn(index, { name: e.target.value })}
                      placeholder="column_name"
                      className="h-7 flex-1 font-mono text-xs"
                    />
                    <Input
                      value={col.data_type ?? ""}
                      onChange={(e) => setColumn(index, { data_type: e.target.value || null })}
                      placeholder="type"
                      className="h-7 w-20 text-xs"
                    />
                    <Button variant="ghost" size="icon" className="size-7" onClick={() => removeColumn(index)}>
                      <Trash2 className="size-3.5 text-muted-foreground" aria-hidden="true" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 text-xs">
                    <label className="flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={Boolean(col.is_primary_key)}
                        onChange={(e) => setColumn(index, { is_primary_key: e.target.checked })}
                      />
                      Primary key
                    </label>
                    <label className="flex items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={Boolean(col.is_foreign_key)}
                        onChange={(e) => setColumn(index, { is_foreign_key: e.target.checked })}
                      />
                      Foreign key
                    </label>
                  </div>
                  {col.is_foreign_key ? (
                    <div className="flex items-center gap-1.5">
                      <Select
                        value={col.references_table ?? ""}
                        onChange={(e) => setColumn(index, { references_table: e.target.value || null })}
                        className="h-7 flex-1 text-xs"
                      >
                        <option value="">references table…</option>
                        {otherTableNames.map((name) => (
                          <option key={name} value={name}>
                            {name}
                          </option>
                        ))}
                      </Select>
                      <Input
                        value={col.references_column ?? ""}
                        onChange={(e) => setColumn(index, { references_column: e.target.value || null })}
                        placeholder="column"
                        className="h-7 w-24 font-mono text-xs"
                      />
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>

          <Button variant="destructive" size="sm" onClick={onDelete}>
            <Trash2 className="size-3.5" aria-hidden="true" />
            Delete table
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
