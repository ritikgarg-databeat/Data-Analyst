"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface StageInfo {
  id: string;
  label: string;
  purpose: string;
  example: string;
  technology: string;
  commonFailure: string;
  analystInteraction: string;
}

const STAGES: StageInfo[] = [
  {
    id: "api",
    label: "API / Source",
    purpose: "Where the data is produced — an application database, a third-party API, an event stream, a file drop.",
    example: "An ecommerce app's orders/payments tables, or a marketing platform's campaign-performance API.",
    technology: "Postgres/MySQL, REST/GraphQL APIs, webhooks, event streams (Kafka), flat-file exports.",
    commonFailure: "A source schema changes (a column renamed or dropped) with no warning to anything downstream.",
    analystInteraction:
      "Rarely touched directly — but knowing what a source actually is (and its update cadence) explains a lot about why a number lags reality.",
  },
  {
    id: "raw",
    label: "Raw / Landing",
    purpose: "An unmodified copy of source data, ingested as-is — the first stop before any transformation.",
    example: "A nightly dump of orders.csv, or a raw JSON blob of API responses, stored exactly as received.",
    technology: "Object storage (S3/GCS/Azure Blob), a raw schema in the warehouse, a data lake.",
    commonFailure: "An ingestion job silently fails partway through, landing a truncated or duplicated file.",
    analystInteraction:
      "Usually off-limits for querying directly (unstructured/unclean) — but the first place to check when a downstream number looks wrong.",
  },
  {
    id: "staging",
    label: "Staging",
    purpose: "Light cleanup and standardization — renaming, casting types, trimming/lowercasing text — with minimal business logic.",
    example: 'stg_orders.sql: trim(lower(status)) as status — the real staging convention this project\'s dbt project uses.',
    technology: "dbt staging models, views (cheap to keep fresh, no storage cost for unchanged logic).",
    commonFailure: "A staging model silently passes through a dirty value instead of standardizing it, and every downstream model inherits the mess.",
    analystInteraction:
      "The layer analysts should feel most comfortable reading and writing — this is exactly what the dbt Lab's staging models teach.",
  },
  {
    id: "transform",
    label: "Transform",
    purpose: "Business logic: joins, aggregations, derived metrics — turning clean staging data into something analysis-ready.",
    example: "int_order_items_priced.sql joining order items to products to compute line-level margin.",
    technology: "dbt intermediate/marts models, materialized as tables for performance.",
    commonFailure: "A join fans out rows unexpectedly (a one-to-many relationship treated as one-to-one), silently inflating a sum.",
    analystInteraction:
      "Core analyst territory — writing and reviewing these models is the single highest-leverage skill this phase teaches.",
  },
  {
    id: "warehouse",
    label: "Warehouse",
    purpose: "Where transformed models actually live and get queried from — the durable, structured store everything else reads from.",
    example: "A DuckDB file locally in this lab; BigQuery/Snowflake/Databricks in a real company.",
    technology: "Cloud data warehouses, or (as in this lab) a local DuckDB file for a zero-cost, zero-setup equivalent.",
    commonFailure: "A model that should have refreshed didn't (a broken scheduled job), so the warehouse serves stale data with no obvious signal that it's stale.",
    analystInteraction:
      "Where SQL Lab queries actually run against — understanding its layout (staging/intermediate/marts schemas) is what makes the schema explorer make sense.",
  },
  {
    id: "mart",
    label: "Mart",
    purpose: "A curated, often department-scoped subset of the warehouse — the final, presentation-ready tables.",
    example: "fct_orders, dim_customers, dim_products — this project's real marts, ready for direct querying or a dashboard.",
    technology: "dbt marts models (materialized as tables), sometimes a separate physical data mart.",
    commonFailure: "Two marts compute 'the same' metric slightly differently (different filters), and nobody notices until two dashboards disagree.",
    analystInteraction:
      "The layer most day-to-day analysis and dashboards should be built on — not raw or staging tables.",
  },
  {
    id: "dashboard",
    label: "Dashboard / BI",
    purpose: "The last mile — where a mart's numbers reach an actual stakeholder, as a chart, table, or KPI.",
    example: "A revenue-by-channel dashboard built directly on fct_orders and dim_products.",
    technology: "BI tools (Looker, Tableau, Power BI, Metabase) or this platform's own Visualization workspace.",
    commonFailure: "A dashboard is left pointed at a deprecated mart after a rename, quietly going stale while looking fine.",
    analystInteraction: "Where most stakeholders experience your work — but only as good as the mart it's built on.",
  },
];

/** A lightweight, non-editable reference diagram of a typical pipeline's stages — distinct from the
 * graph-builder above, which is for designing a specific pipeline, not learning the generic shape of one. */
export function PipelineStageReference() {
  const [selectedId, setSelectedId] = useState<string>(STAGES[0].id);
  const selected = STAGES.find((s) => s.id === selectedId)!;

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="mb-3 text-sm font-semibold text-foreground">A typical pipeline, stage by stage</p>
      <div className="flex flex-wrap items-center gap-1.5">
        {STAGES.map((stage, index) => (
          <div key={stage.id} className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setSelectedId(stage.id)}
              className={cn(
                "rounded-md border px-3 py-1.5 text-xs font-medium transition-colors",
                selectedId === stage.id
                  ? "border-primary bg-primary/10 text-foreground"
                  : "border-border text-muted-foreground hover:bg-accent/50",
              )}
            >
              {stage.label}
            </button>
            {index < STAGES.length - 1 ? <span className="text-muted-foreground">→</span> : null}
          </div>
        ))}
      </div>

      <div className="mt-4 space-y-2 rounded-lg border border-border bg-muted/20 p-3 text-sm">
        <div className="flex items-center gap-2">
          <Badge>{selected.label}</Badge>
        </div>
        <p>
          <span className="font-medium text-foreground">Purpose: </span>
          <span className="text-muted-foreground">{selected.purpose}</span>
        </p>
        <p>
          <span className="font-medium text-foreground">Example: </span>
          <span className="text-muted-foreground">{selected.example}</span>
        </p>
        <p>
          <span className="font-medium text-foreground">Technology: </span>
          <span className="text-muted-foreground">{selected.technology}</span>
        </p>
        <p>
          <span className="font-medium text-foreground">Common failure: </span>
          <span className="text-muted-foreground">{selected.commonFailure}</span>
        </p>
        <p>
          <span className="font-medium text-foreground">Analyst interaction: </span>
          <span className="text-muted-foreground">{selected.analystInteraction}</span>
        </p>
      </div>
    </div>
  );
}
