"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  BadgeCheck,
  Code2,
  FolderKanban,
  Loader2,
  Microscope,
  PieChart,
  RefreshCw,
  Terminal,
} from "lucide-react";
import type { ColumnProfileSchema, SchemaColumnSchema } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Select } from "@/components/ui/select";
import { useDataset, useTriggerReprofile } from "@/features/datasets/use-datasets";
import { useDatasetProfile, useDatasetQuality } from "@/features/datasets/use-dataset-profile";
import { useDatasetSchema } from "@/features/datasets/use-dataset-schema";
import { useDatasetUsage, useDatasetVersions } from "@/features/datasets/use-dataset-meta";
import { useReimportDataset } from "@/features/datasets/use-datasets";
import { useCreateProjectFromDataset } from "@/features/projects/use-projects";
import { cn } from "@/lib/utils";

import { ColumnDetailSheet } from "./column-detail-sheet";
import { NotesPanel } from "./notes-panel";
import { QualityPanel } from "./quality-panel";
import { RelationshipsPanel } from "./relationships-panel";
import { SchemaViewer } from "./schema-viewer";

const numberFormatter = new Intl.NumberFormat("en-US");

function formatCount(value: number | null): string {
  return value === null ? "—" : numberFormatter.format(value);
}

function formatBytes(bytes: number | null): string | null {
  if (bytes === null) return null;
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

type TabKey = "overview" | "schema" | "quality" | "relationships" | "notes" | "usage";

const TABS: { key: TabKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "schema", label: "Schema" },
  { key: "quality", label: "Quality" },
  { key: "relationships", label: "Relationships" },
  { key: "notes", label: "Notes" },
  { key: "usage", label: "Usage" },
];

export function DatasetDetail({ slug }: { slug: string }) {
  const datasetQuery = useDataset(slug);
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<TabKey>("overview");
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [selectedColumn, setSelectedColumn] = useState<ColumnProfileSchema | null>(null);

  const dataset = datasetQuery.data;
  const activeTable = selectedTable ?? dataset?.tables[0]?.table_name ?? undefined;

  // The schema/profile/quality/etc. queries below each fetch once and cache
  // for staleTime — if this page is opened right after import, that first
  // fetch can land while the dataset is still IMPORTING/PROFILING (before
  // any DatasetTable/profile rows exist) and nothing would ever tell them to
  // look again. `useDataset` already polls until the parent dataset settles;
  // the moment it does, explicitly invalidate everything scoped under this
  // dataset so schema/profile/quality (etc.) refetch with the now-real data.
  const previousStatusRef = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (!dataset) return;
    const previous = previousStatusRef.current;
    const wasSettling = previous === "IMPORTING" || previous === "PROFILING";
    if (wasSettling && dataset.status !== previous) {
      void queryClient.invalidateQueries({ queryKey: ["datasets", "detail", dataset.slug] });
    }
    previousStatusRef.current = dataset.status;
  }, [dataset, queryClient]);

  const schemaQuery = useDatasetSchema(dataset?.slug, activeTable);
  const profileQuery = useDatasetProfile(dataset?.slug);
  const qualityQuery = useDatasetQuality(dataset?.slug);
  const versionsQuery = useDatasetVersions(dataset?.slug);
  const usageQuery = useDatasetUsage(dataset?.slug);
  const reprofileMutation = useTriggerReprofile(dataset?.slug ?? "");
  const reimportMutation = useReimportDataset(dataset?.slug ?? "");
  const createProject = useCreateProjectFromDataset();
  const [projectCreated, setProjectCreated] = useState(false);
  const reimportInputRef = useRef<HTMLInputElement>(null);

  const activeQualityReport = useMemo(
    () => qualityQuery.data?.tables.find((t) => t.table_name === activeTable) ?? qualityQuery.data?.tables[0],
    [qualityQuery.data, activeTable],
  );

  function handleSelectColumn(column: SchemaColumnSchema) {
    const tableProfile = profileQuery.data?.tables.find((t) => t.table_name === activeTable);
    const fullColumn = tableProfile?.columns.find((c) => c.column_name === column.column_name);
    setSelectedColumn(fullColumn ?? null);
  }

  if (datasetQuery.isLoading) {
    return <LoadingState count={1} itemClassName="h-96" />;
  }

  if (datasetQuery.isError || !dataset) {
    return (
      <ErrorState
        title="Unable to load this dataset"
        message="We couldn't reach the API, or this dataset doesn't exist."
        retry={() => void datasetQuery.refetch()}
      />
    );
  }

  const latestTwoVersions = (versionsQuery.data ?? []).slice(0, 2);
  const changed = dataset.version > 1 && latestTwoVersions.length === 2;

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground">{dataset.name}</h1>
            {dataset.business_domain ? <Badge variant="outline">{dataset.business_domain}</Badge> : null}
            <Badge variant="secondary">{dataset.difficulty.toLowerCase()}</Badge>
            {dataset.source_type === "KAGGLE" ? <Badge variant="outline">Kaggle</Badge> : null}
            {dataset.version > 1 ? <Badge variant="outline">v{dataset.version}</Badge> : null}
          </div>
          {dataset.description ? <p className="max-w-2xl text-sm text-muted-foreground">{dataset.description}</p> : null}
          <p className="text-sm text-muted-foreground">
            {formatCount(dataset.row_count)} rows · {formatCount(dataset.column_count)} columns
            {formatBytes(dataset.size_bytes) ? ` · ${formatBytes(dataset.size_bytes)}` : ""}
            {dataset.tables.length > 1 ? ` · ${dataset.tables.length} tables` : ""}
            {" · Source: "}
            {dataset.source ?? "local upload"}
          </p>
          {dataset.tags.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {dataset.tags.map((tag) => (
                <Badge key={tag} variant="outline">
                  {tag}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/eda?dataset=${dataset.id}`}>
              <Microscope className="size-4" aria-hidden="true" />
              Open EDA
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={`/visualization?dataset=${dataset.id}`}>
              <PieChart className="size-4" aria-hidden="true" />
              Visualize
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={`/sql-lab?database=${dataset.slug}`}>
              <Terminal className="size-4" aria-hidden="true" />
              SQL Lab
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href="/python-lab">
              <Code2 className="size-4" aria-hidden="true" />
              Python Lab
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link href={`/data-quality?dataset=${dataset.id}`}>
              <BadgeCheck className="size-4" aria-hidden="true" />
              Quality Lab
            </Link>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              createProject.mutate(
                { datasetId: dataset.id, payload: {} },
                { onSuccess: () => setProjectCreated(true) },
              )
            }
            disabled={createProject.isPending || projectCreated}
          >
            <FolderKanban className="size-4" aria-hidden="true" />
            {projectCreated ? "Project created" : "Create Project"}
          </Button>
          <input
            ref={reimportInputRef}
            type="file"
            multiple
            accept=".csv,.parquet,.json,.xlsx"
            className="sr-only"
            onChange={(event) => {
              if (event.target.files && event.target.files.length > 0) {
                reimportMutation.mutate(Array.from(event.target.files));
              }
              event.target.value = "";
            }}
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => reimportInputRef.current?.click()}
            disabled={reimportMutation.isPending}
          >
            <RefreshCw className={cn("size-4", reimportMutation.isPending && "animate-spin")} aria-hidden="true" />
            Update Data
          </Button>
        </div>
      </div>

      {dataset.status === "IMPORTING" || dataset.status === "PROFILING" ? (
        <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/40 px-4 py-2.5 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          {dataset.status === "IMPORTING" ? "Importing files…" : "Profiling data…"} This page updates automatically.
        </div>
      ) : null}
      {dataset.status === "FAILED" ? (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-2.5 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <div>
            <p className="font-medium">Import failed</p>
            <p>{dataset.status_message}</p>
          </div>
        </div>
      ) : null}
      {changed ? (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-warning/40 bg-warning/10 px-4 py-2.5 text-sm">
          <span>
            Dataset changed — now on <strong>v{latestTwoVersions[0].version}</strong>, previously v
            {latestTwoVersions[1].version}.
          </span>
          <button type="button" className="font-medium text-primary hover:underline" onClick={() => setTab("overview")}>
            Review changes
          </button>
        </div>
      ) : null}

      <div role="tablist" className="flex flex-wrap gap-1 border-b border-border">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
              tab === t.key
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {dataset.tables.length > 1 && (tab === "schema" || tab === "quality") ? (
        <div className="flex items-center gap-2">
          <label htmlFor="table-select" className="text-sm text-muted-foreground">
            Table
          </label>
          <Select
            id="table-select"
            value={activeTable}
            onChange={(event) => setSelectedTable(event.target.value)}
            className="w-full sm:w-48"
          >
            {dataset.tables.map((t) => (
              <option key={t.table_name} value={t.table_name}>
                {t.table_name} ({formatCount(t.row_count)} rows)
              </option>
            ))}
          </Select>
        </div>
      ) : null}

      <div role="tabpanel">
        {tab === "overview" ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-border bg-card p-4">
              <p className="mb-2 text-sm font-semibold text-foreground">Tables</p>
              <ul className="flex flex-col gap-1.5">
                {dataset.tables.map((t) => (
                  <li key={t.table_name} className="flex items-center justify-between text-sm">
                    <span className="font-mono text-foreground">{t.table_name}</span>
                    <span className="text-muted-foreground">
                      {formatCount(t.row_count)} rows · {formatCount(t.column_count)} cols
                    </span>
                  </li>
                ))}
              </ul>
              {dataset.tables[0]?.grain ? (
                <p className="mt-2 text-xs text-muted-foreground">Grain: {dataset.tables[0].grain}</p>
              ) : null}
            </div>
            <div className="rounded-xl border border-border bg-card p-4">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-semibold text-foreground">Overall quality</p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => reprofileMutation.mutate()}
                  disabled={reprofileMutation.isPending}
                >
                  <RefreshCw className={cn("size-3.5", reprofileMutation.isPending && "animate-spin")} />
                  Re-profile
                </Button>
              </div>
              {qualityQuery.data && qualityQuery.data.tables.length > 0 ? (
                <ul className="flex flex-col gap-1">
                  {qualityQuery.data.tables.map((r) => (
                    <li key={r.table_name} className="flex items-center justify-between text-sm">
                      <span className="font-mono">{r.table_name}</span>
                      <span className="font-medium tabular-nums">{r.overall_score.toFixed(0)}%</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-muted-foreground">Not profiled yet.</p>
              )}
            </div>
          </div>
        ) : null}

        {tab === "schema" ? (
          schemaQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-64" />
          ) : schemaQuery.isError ? (
            <ErrorState
              title="Unable to load schema"
              message="We couldn't reach the API to load this table's schema."
              retry={() => void schemaQuery.refetch()}
            />
          ) : schemaQuery.data && schemaQuery.data.length > 0 ? (
            <SchemaViewer columns={schemaQuery.data[0].columns} onSelectColumn={handleSelectColumn} />
          ) : (
            <p className="text-sm text-muted-foreground">This table hasn&apos;t been profiled yet.</p>
          )
        ) : null}

        {tab === "quality" ? (
          qualityQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-64" />
          ) : qualityQuery.isError ? (
            <ErrorState
              title="Unable to load data quality"
              message="We couldn't reach the API to load this table's quality report."
              retry={() => void qualityQuery.refetch()}
            />
          ) : activeQualityReport ? (
            <QualityPanel datasetSlug={dataset.slug} report={activeQualityReport} />
          ) : (
            <p className="text-sm text-muted-foreground">This table hasn&apos;t been profiled yet.</p>
          )
        ) : null}

        {tab === "relationships" ? <RelationshipsPanel dataset={dataset} /> : null}

        {tab === "notes" ? <NotesPanel datasetSlug={dataset.slug} /> : null}

        {tab === "usage" ? (
          usageQuery.data ? (
            <div className="rounded-xl border border-border bg-card p-4">
              <p className="mb-3 text-sm font-semibold text-foreground">Used in</p>
              <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {[
                  ["SQL Exercises", usageQuery.data.sql_exercises],
                  ["Python Exercises", usageQuery.data.python_exercises],
                  ["EDA Workspaces", usageQuery.data.eda_workspaces],
                  ["Charts", usageQuery.data.charts],
                  ["Projects", usageQuery.data.projects],
                  ["Other Exercises", usageQuery.data.other_exercises],
                ].map(([label, value]) => (
                  <div key={label as string}>
                    <dt className="text-xs text-muted-foreground">{label}</dt>
                    <dd className="text-lg font-semibold text-foreground">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ) : (
            <LoadingState count={1} itemClassName="h-32" />
          )
        ) : null}
      </div>

      <ColumnDetailSheet
        datasetSlug={dataset.slug}
        tableName={activeTable ?? ""}
        column={selectedColumn}
        onOpenChange={(open) => {
          if (!open) setSelectedColumn(null);
        }}
      />
    </div>
  );
}
