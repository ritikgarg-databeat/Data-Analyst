"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import type { AddEvidenceRequest, Evidence, EvidenceType } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

const EVIDENCE_TYPE_LABELS: Record<EvidenceType, string> = {
  SQL_QUERY: "SQL query",
  PYTHON_EXECUTION: "Python execution",
  CHART: "Chart",
  STATISTIC: "Statistic",
  DATASET: "Dataset",
  DATA_MODEL: "Data model",
  DBT_MODEL: "dbt model",
};

/**
 * Evidence links a Finding/Hypothesis back to the real artifact that
 * supports it (spec sections 15-16, 52). `snapshot` is denormalized text
 * (a query, a stat's value, a chart's title) so the evidence stays
 * meaningful even if the referenced row is later deleted — there is no
 * live join back to SqlQueryHistory/PythonExecution/Chart here on purpose.
 */
export function EvidenceList({
  evidence,
  onAdd,
  onDelete,
  adding,
}: {
  evidence: Evidence[];
  onAdd: (payload: AddEvidenceRequest) => void;
  onDelete: (evidenceId: string) => void;
  adding?: boolean;
}) {
  const [showForm, setShowForm] = useState(false);
  const [evidenceType, setEvidenceType] = useState<EvidenceType>("SQL_QUERY");
  const [label, setLabel] = useState("");
  const [snapshot, setSnapshot] = useState("");

  const submit = () => {
    if (!label.trim()) return;
    onAdd({ evidence_type: evidenceType, label: label.trim(), snapshot: snapshot.trim() || undefined });
    setLabel("");
    setSnapshot("");
    setShowForm(false);
  };

  return (
    <div className="mt-2 space-y-1.5 border-l-2 border-border pl-3">
      {evidence.map((item) => (
        <div key={item.id} className="flex items-start justify-between gap-2 text-xs">
          <div>
            <span className="font-medium text-foreground">{EVIDENCE_TYPE_LABELS[item.evidence_type]}:</span>{" "}
            <span className="text-muted-foreground">{item.label}</span>
            {item.snapshot ? (
              <pre className="mt-0.5 max-w-md overflow-x-auto rounded bg-muted px-2 py-1 font-mono text-[11px] whitespace-pre-wrap text-muted-foreground">
                {item.snapshot}
              </pre>
            ) : null}
          </div>
          <button
            type="button"
            onClick={() => onDelete(item.id)}
            className="shrink-0 text-muted-foreground hover:text-destructive"
            aria-label="Remove evidence"
          >
            <Trash2 className="size-3.5" aria-hidden="true" />
          </button>
        </div>
      ))}

      {showForm ? (
        <div className="flex flex-col gap-1.5 rounded-md border border-border bg-card p-2">
          <div className="flex gap-1.5">
            <Select
              value={evidenceType}
              onChange={(e) => setEvidenceType(e.target.value as EvidenceType)}
              className="h-7 text-xs"
            >
              {Object.entries(EVIDENCE_TYPE_LABELS).map(([value, label2]) => (
                <option key={value} value={value}>
                  {label2}
                </option>
              ))}
            </Select>
            <Input
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="What does this show?"
              className="h-7 text-xs"
            />
          </div>
          <Input
            value={snapshot}
            onChange={(e) => setSnapshot(e.target.value)}
            placeholder="Optional: paste the query/code/value"
            className="h-7 text-xs"
          />
          <div className="flex gap-1.5">
            <Button type="button" size="sm" onClick={submit} disabled={adding}>
              Add evidence
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
          </div>
        </div>
      ) : (
        <Button type="button" size="sm" variant="ghost" onClick={() => setShowForm(true)} className="h-6 px-1.5 text-xs">
          <Plus className="size-3" aria-hidden="true" />
          Attach evidence
        </Button>
      )}
    </div>
  );
}
