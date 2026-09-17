"use client";

import { useState } from "react";
import { CheckCircle2, ClipboardList, Trash2, XCircle } from "lucide-react";
import type { DataQualityRuleType } from "@data-analyst-lab/shared";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { useDatasets } from "@/features/datasets/use-datasets";
import {
  useCreateDataQualityRule,
  useDataQualityRuns,
  useDataQualityRules,
  useDeleteDataQualityRule,
  useRunDataQualityRule,
} from "@/features/data-quality/use-data-quality-rules";
import { useSqlTables } from "@/features/sql/use-sql-tables";
import { cn } from "@/lib/utils";

import { RuleConfigFields, toConfigPayload, type RuleConfigValue } from "./rule-config-fields";

const RULE_TYPES: DataQualityRuleType[] = [
  "NOT_NULL",
  "UNIQUE",
  "ACCEPTED_VALUES",
  "RELATIONSHIP",
  "MIN_MAX",
  "FRESHNESS",
  "ROW_COUNT",
];

function RunHistory({ ruleId }: { ruleId: string }) {
  const runsQuery = useDataQualityRuns(ruleId);
  if (runsQuery.isLoading) return <LoadingState count={1} itemClassName="h-6" />;
  if (runsQuery.isError) {
    return (
      <div className="px-3 pb-2">
        <ErrorState
          title="Unable to load run history"
          message="We couldn't reach the API to load this rule's run history."
          retry={() => void runsQuery.refetch()}
        />
      </div>
    );
  }
  if (!runsQuery.data || runsQuery.data.length === 0) {
    return <p className="px-3 pb-2 text-xs text-muted-foreground">No runs yet.</p>;
  }
  return (
    <ul className="space-y-1 px-3 pb-2">
      {runsQuery.data.map((run) => (
        <li key={run.id} className="flex items-center gap-2 text-xs">
          {run.status === "PASS" ? (
            <CheckCircle2 className="size-3.5 shrink-0 text-success" aria-hidden="true" />
          ) : (
            <XCircle className="size-3.5 shrink-0 text-destructive" aria-hidden="true" />
          )}
          <span className="text-muted-foreground">{new Date(run.executed_at).toLocaleString()}</span>
          {run.actual_value ? <span className="truncate text-foreground">{run.actual_value}</span> : null}
        </li>
      ))}
    </ul>
  );
}

interface DataQualityWorkspaceProps {
  /** Pre-selects the dataset dropdown — used by the `?dataset=` deep link from a dataset's page. */
  initialDatasetId?: string;
}

/** The Data Quality Lab: build a rule, run it for real against a dataset's own DuckDB-backed table, see the result. */
export function DataQualityWorkspace({ initialDatasetId }: DataQualityWorkspaceProps = {}) {
  const datasetsQuery = useDatasets();
  const [datasetId, setDatasetId] = useState(initialDatasetId ?? "");
  const [tableName, setTableName] = useState("");
  const [columnName, setColumnName] = useState("");
  const [ruleName, setRuleName] = useState("");
  const [ruleType, setRuleType] = useState<DataQualityRuleType>("NOT_NULL");
  const [config, setConfig] = useState<RuleConfigValue>({});
  const [expandedRuleId, setExpandedRuleId] = useState<string | null>(null);

  const selectedDataset = datasetsQuery.data?.find((d) => d.id === datasetId);
  const tablesQuery = useSqlTables(selectedDataset?.slug ?? "", "duckdb");
  const rulesQuery = useDataQualityRules(datasetId || undefined);
  const createRule = useCreateDataQualityRule();
  const deleteRule = useDeleteDataQualityRule();
  const runRule = useRunDataQualityRule();

  const needsColumn = ruleType !== "ROW_COUNT";
  const canCreate = Boolean(datasetId && tableName && (!needsColumn || columnName));

  function handleCreate() {
    if (!canCreate) return;
    createRule.mutate(
      {
        dataset_id: datasetId,
        table_name: tableName,
        column_name: needsColumn ? columnName : null,
        rule_type: ruleType,
        config: toConfigPayload(ruleType, config),
        name: ruleName.trim() || null,
      },
      {
        onSuccess: () => {
          setConfig({});
          setRuleName("");
        },
      },
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[22rem_1fr]">
      <div className="space-y-4 rounded-xl border border-border bg-card p-4">
        <p className="text-sm font-semibold text-foreground">New rule</p>

        <div className="space-y-1">
          <Label htmlFor="dq-dataset">Dataset</Label>
          <Select
            id="dq-dataset"
            value={datasetId}
            onChange={(e) => {
              setDatasetId(e.target.value);
              setTableName("");
            }}
          >
            <option value="">Choose a dataset…</option>
            {(datasetsQuery.data ?? [])
              .filter((d) => d.status === "READY")
              .map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
          </Select>
        </div>

        <div className="space-y-1">
          <Label htmlFor="dq-table">Table</Label>
          <Select
            id="dq-table"
            value={tableName}
            onChange={(e) => setTableName(e.target.value)}
            disabled={!datasetId}
          >
            <option value="">Choose a table…</option>
            {(tablesQuery.data ?? []).map((t) => (
              <option key={t.table_name} value={t.table_name}>
                {t.table_name}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-1">
          <Label htmlFor="dq-rule-type">Rule type</Label>
          <Select
            id="dq-rule-type"
            value={ruleType}
            onChange={(e) => {
              setRuleType(e.target.value as DataQualityRuleType);
              setConfig({});
            }}
          >
            {RULE_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </Select>
        </div>

        {needsColumn ? (
          <div className="space-y-1">
            <Label htmlFor="dq-column">Column</Label>
            <Input
              id="dq-column"
              value={columnName}
              onChange={(e) => setColumnName(e.target.value)}
              placeholder="e.g. order_id"
              className="font-mono text-xs"
            />
          </div>
        ) : null}

        <RuleConfigFields ruleType={ruleType} value={config} onChange={setConfig} />

        <div className="space-y-1">
          <Label htmlFor="dq-name">Name (optional)</Label>
          <Input
            id="dq-name"
            value={ruleName}
            onChange={(e) => setRuleName(e.target.value)}
            placeholder="e.g. Orders must have a customer"
          />
        </div>

        <Button onClick={handleCreate} disabled={!canCreate || createRule.isPending} className="w-full">
          {createRule.isPending ? "Creating…" : "Create rule"}
        </Button>
      </div>

      <div className="space-y-3">
        <p className="text-sm font-semibold text-foreground">Rules{datasetId ? " for this dataset" : ""}</p>
        {rulesQuery.isLoading ? (
          <LoadingState count={3} itemClassName="h-14" />
        ) : rulesQuery.isError ? (
          <ErrorState retry={() => void rulesQuery.refetch()} />
        ) : !rulesQuery.data || rulesQuery.data.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No rules yet"
            description="Create a rule on the left, then run it against the real data."
          />
        ) : (
          <ul className="divide-y divide-border rounded-lg border border-border">
            {rulesQuery.data.map((rule) => {
              const isOpen = expandedRuleId === rule.id;
              return (
                <li key={rule.id}>
                  <div className="flex items-center gap-2 px-3 py-2">
                    <button
                      type="button"
                      onClick={() => setExpandedRuleId(isOpen ? null : rule.id)}
                      className="flex flex-1 items-center gap-2 text-left"
                    >
                      <Badge variant="outline">{rule.rule_type}</Badge>
                      {rule.name ? <span className="text-sm text-foreground">{rule.name}</span> : null}
                      <span className={cn("font-mono text-sm", rule.name ? "text-muted-foreground" : "text-foreground")}>
                        {rule.table_name}
                        {rule.column_name ? `.${rule.column_name}` : ""}
                      </span>
                    </button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => runRule.mutate(rule.id)}
                      disabled={runRule.isPending}
                    >
                      Run
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label="Delete rule"
                      onClick={() => deleteRule.mutate(rule.id)}
                    >
                      <Trash2 className="size-4 text-muted-foreground" aria-hidden="true" />
                    </Button>
                  </div>
                  {isOpen ? <RunHistory ruleId={rule.id} /> : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
