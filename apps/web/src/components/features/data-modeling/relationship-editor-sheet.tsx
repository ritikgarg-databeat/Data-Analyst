"use client";

import { Trash2 } from "lucide-react";
import type { DataModelKind, DataModelRelationshipType } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";

export interface RelationshipEdgeData {
  from_column: string | null;
  to_column: string | null;
  relationship_type: DataModelRelationshipType;
  label: string | null;
  [key: string]: unknown;
}

const RELATIONSHIP_TYPES_BY_KIND: Record<DataModelKind, DataModelRelationshipType[]> = {
  DIMENSIONAL: ["ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY"],
  ARCHITECTURE: ["FLOW", "ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY"],
  PIPELINE: ["DEPENDS_ON"],
};

interface RelationshipEditorSheetProps {
  modelKind: DataModelKind;
  open: boolean;
  data: RelationshipEdgeData | null;
  fromTableName: string;
  toTableName: string;
  onChange: (next: RelationshipEdgeData) => void;
  onDelete: () => void;
  onOpenChange: (open: boolean) => void;
}

export function RelationshipEditorSheet({
  modelKind,
  open,
  data,
  fromTableName,
  toTableName,
  onChange,
  onDelete,
  onOpenChange,
}: RelationshipEditorSheetProps) {
  if (!data) return null;

  function set<K extends keyof RelationshipEdgeData>(key: K, value: RelationshipEdgeData[K]) {
    onChange({ ...data!, [key]: value });
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:w-96">
        <SheetHeader>
          <SheetTitle>
            {fromTableName} → {toTableName}
          </SheetTitle>
        </SheetHeader>
        <div className="flex-1 space-y-4 overflow-y-auto px-4 pb-4">
          <div className="space-y-1">
            <Label htmlFor="rel-type">Relationship type</Label>
            <Select
              id="rel-type"
              value={data.relationship_type}
              onChange={(e) => set("relationship_type", e.target.value as DataModelRelationshipType)}
            >
              {RELATIONSHIP_TYPES_BY_KIND[modelKind].map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>
          </div>

          {modelKind === "DIMENSIONAL" ? (
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label htmlFor="rel-from-column">{fromTableName} column</Label>
                <Input
                  id="rel-from-column"
                  value={data.from_column ?? ""}
                  onChange={(e) => set("from_column", e.target.value || null)}
                  className="font-mono text-xs"
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="rel-to-column">{toTableName} column</Label>
                <Input
                  id="rel-to-column"
                  value={data.to_column ?? ""}
                  onChange={(e) => set("to_column", e.target.value || null)}
                  className="font-mono text-xs"
                />
              </div>
            </div>
          ) : null}

          <div className="space-y-1">
            <Label htmlFor="rel-label">Label</Label>
            <Input
              id="rel-label"
              value={data.label ?? ""}
              onChange={(e) => set("label", e.target.value || null)}
              placeholder="optional"
            />
          </div>

          <Button variant="destructive" size="sm" onClick={onDelete}>
            <Trash2 className="size-3.5" aria-hidden="true" />
            Delete relationship
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
