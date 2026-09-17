"use client";

import { useId } from "react";

import { Textarea } from "@/components/ui/textarea";

export function parseNumberList(raw: string): number[] {
  return raw
    .split(/[\s,]+/)
    .map((s) => s.trim())
    .filter(Boolean)
    .map(Number)
    .filter((n) => Number.isFinite(n));
}

interface NumberListInputProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

/** A plain textarea for pasting a list of numbers (comma/space/newline separated) — the
 * simplest, always-available input mode for the Statistics tools (spec section 55). */
export function NumberListInput({ label, value, onChange, placeholder }: NumberListInputProps) {
  const id = useId();
  const count = parseNumberList(value).length;
  return (
    <div className="flex flex-col gap-1">
      {label ? (
        <div className="flex items-center justify-between">
          <label htmlFor={id} className="text-xs font-medium text-muted-foreground">
            {label}
          </label>
          <span className="text-xs text-muted-foreground">{count} value{count === 1 ? "" : "s"}</span>
        </div>
      ) : null}
      <Textarea
        id={id}
        aria-label={label || undefined}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder ?? "e.g. 12, 15, 9, 22, 18, 30"}
        className="min-h-20 font-mono text-xs"
      />
    </div>
  );
}
