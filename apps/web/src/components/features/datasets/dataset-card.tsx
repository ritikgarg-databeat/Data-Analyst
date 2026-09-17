import Link from "next/link";
import { CheckCircle2, CircleDashed, Database, Loader2, XCircle } from "lucide-react";
import type { Dataset } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

const DIFFICULTY_VARIANT = {
  BEGINNER: "outline",
  INTERMEDIATE: "secondary",
  ADVANCED: "default",
} as const;

const numberFormatter = new Intl.NumberFormat("en-US");

function formatCount(value: number | null): string {
  return value === null ? "—" : numberFormatter.format(value);
}

function formatBytes(bytes: number | null): string | null {
  if (bytes === null) return null;
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StatusBadge({ status }: { status: Dataset["status"] }) {
  switch (status) {
    case "READY":
      return null; // the default, quiet state — no badge needed
    case "IMPORTING":
    case "PROFILING":
      return (
        <Badge variant="secondary" className="gap-1">
          <Loader2 className="size-3 animate-spin" aria-hidden="true" />
          {status === "IMPORTING" ? "Importing" : "Profiling"}
        </Badge>
      );
    case "FAILED":
      return (
        <Badge variant="destructive" className="gap-1">
          <XCircle className="size-3" aria-hidden="true" />
          Failed
        </Badge>
      );
    case "ARCHIVED":
      return <Badge variant="outline">Archived</Badge>;
    default:
      return null;
  }
}

export function DatasetCard({ dataset }: { dataset: Dataset }) {
  const sizeLabel = formatBytes(dataset.size_bytes);
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <Database className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            <Link
              href={`/datasets/${dataset.slug}`}
              className="truncate font-semibold text-foreground hover:underline"
            >
              {dataset.name}
            </Link>
          </div>
          <StatusBadge status={dataset.status} />
        </div>
        <p className="text-xs text-muted-foreground">
          {formatCount(dataset.row_count)} rows · {formatCount(dataset.column_count)} columns
          {sizeLabel ? ` · ${sizeLabel}` : ""}
        </p>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        {dataset.description ? (
          <p className="line-clamp-2 text-sm text-muted-foreground">{dataset.description}</p>
        ) : null}

        <div className="flex flex-wrap items-center gap-1.5">
          {dataset.business_domain ? <Badge variant="outline">{dataset.business_domain}</Badge> : null}
          <Badge variant={DIFFICULTY_VARIANT[dataset.difficulty]}>{dataset.difficulty.toLowerCase()}</Badge>
          {dataset.tables.length > 1 ? (
            <Badge variant="outline">{dataset.tables.length} tables</Badge>
          ) : null}
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span
            className={
              dataset.sql_ready
                ? "flex items-center gap-1 text-success"
                : "flex items-center gap-1 text-muted-foreground"
            }
          >
            {dataset.sql_ready ? (
              <CheckCircle2 className="size-3.5" aria-hidden="true" />
            ) : (
              <CircleDashed className="size-3.5" aria-hidden="true" />
            )}
            SQL Ready
          </span>
          <span
            className={
              dataset.python_ready
                ? "flex items-center gap-1 text-success"
                : "flex items-center gap-1 text-muted-foreground"
            }
          >
            {dataset.python_ready ? (
              <CheckCircle2 className="size-3.5" aria-hidden="true" />
            ) : (
              <CircleDashed className="size-3.5" aria-hidden="true" />
            )}
            Python Ready
          </span>
        </div>

        <Link
          href={`/datasets/${dataset.slug}`}
          className="mt-1 text-sm font-medium text-primary hover:underline"
        >
          Open Dataset →
        </Link>
      </CardContent>
    </Card>
  );
}
