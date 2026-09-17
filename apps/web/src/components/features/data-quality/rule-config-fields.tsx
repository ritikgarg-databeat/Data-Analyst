"use client";

import type { DataQualityRuleType } from "@data-analyst-lab/shared";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export interface RuleConfigValue {
  values?: string; // comma-separated, for ACCEPTED_VALUES
  to_table?: string;
  to_column?: string;
  min?: string;
  max?: string;
  min_rows?: string;
  max_rows?: string;
  as_of?: string;
  max_age_hours?: string;
}

interface RuleConfigFieldsProps {
  ruleType: DataQualityRuleType;
  value: RuleConfigValue;
  onChange: (next: RuleConfigValue) => void;
}

/** Renders only the config inputs relevant to the selected rule type — mirrors app/data_quality/engine.py's
 * per-rule-type config requirements exactly (accepted values / relationship target / min-max / row count / freshness). */
export function RuleConfigFields({ ruleType, value, onChange }: RuleConfigFieldsProps) {
  function set(patch: Partial<RuleConfigValue>) {
    onChange({ ...value, ...patch });
  }

  if (ruleType === "ACCEPTED_VALUES") {
    return (
      <div className="space-y-1">
        <Label htmlFor="dq-values">Accepted values (comma-separated)</Label>
        <Input
          id="dq-values"
          value={value.values ?? ""}
          onChange={(e) => set({ values: e.target.value })}
          placeholder="e.g. completed, pending, cancelled"
        />
      </div>
    );
  }

  if (ruleType === "RELATIONSHIP") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1">
          <Label htmlFor="dq-to-table">References table</Label>
          <Input id="dq-to-table" value={value.to_table ?? ""} onChange={(e) => set({ to_table: e.target.value })} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="dq-to-column">References column</Label>
          <Input
            id="dq-to-column"
            value={value.to_column ?? ""}
            onChange={(e) => set({ to_column: e.target.value })}
          />
        </div>
      </div>
    );
  }

  if (ruleType === "MIN_MAX") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1">
          <Label htmlFor="dq-min">Min (optional)</Label>
          <Input id="dq-min" value={value.min ?? ""} onChange={(e) => set({ min: e.target.value })} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="dq-max">Max (optional)</Label>
          <Input id="dq-max" value={value.max ?? ""} onChange={(e) => set({ max: e.target.value })} />
        </div>
      </div>
    );
  }

  if (ruleType === "ROW_COUNT") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1">
          <Label htmlFor="dq-min-rows">Min rows (optional)</Label>
          <Input id="dq-min-rows" value={value.min_rows ?? ""} onChange={(e) => set({ min_rows: e.target.value })} />
        </div>
        <div className="space-y-1">
          <Label htmlFor="dq-max-rows">Max rows (optional)</Label>
          <Input id="dq-max-rows" value={value.max_rows ?? ""} onChange={(e) => set({ max_rows: e.target.value })} />
        </div>
      </div>
    );
  }

  if (ruleType === "FRESHNESS") {
    return (
      <div className="grid grid-cols-2 gap-2">
        <div className="space-y-1">
          <Label htmlFor="dq-as-of">As of (ISO date, optional)</Label>
          <Input
            id="dq-as-of"
            value={value.as_of ?? ""}
            onChange={(e) => set({ as_of: e.target.value })}
            placeholder="defaults to now"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="dq-max-age">Max age (hours)</Label>
          <Input
            id="dq-max-age"
            value={value.max_age_hours ?? ""}
            onChange={(e) => set({ max_age_hours: e.target.value })}
          />
        </div>
      </div>
    );
  }

  return null; // NOT_NULL / UNIQUE need no config beyond the column
}

/** Converts the form's string-typed config into the JSON body the API expects. */
export function toConfigPayload(ruleType: DataQualityRuleType, value: RuleConfigValue): Record<string, unknown> {
  if (ruleType === "ACCEPTED_VALUES") {
    return { values: (value.values ?? "").split(",").map((v) => v.trim()).filter(Boolean) };
  }
  if (ruleType === "RELATIONSHIP") {
    return { to_table: value.to_table, to_column: value.to_column };
  }
  if (ruleType === "MIN_MAX") {
    const config: Record<string, unknown> = {};
    if (value.min) config.min = Number(value.min);
    if (value.max) config.max = Number(value.max);
    return config;
  }
  if (ruleType === "ROW_COUNT") {
    const config: Record<string, unknown> = {};
    if (value.min_rows) config.min_rows = Number(value.min_rows);
    if (value.max_rows) config.max_rows = Number(value.max_rows);
    return config;
  }
  if (ruleType === "FRESHNESS") {
    const config: Record<string, unknown> = {};
    if (value.as_of) config.as_of = value.as_of;
    if (value.max_age_hours) config.max_age_hours = Number(value.max_age_hours);
    return config;
  }
  return {};
}
