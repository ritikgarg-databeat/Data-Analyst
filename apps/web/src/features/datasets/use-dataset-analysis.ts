import { useQuery } from "@tanstack/react-query";
import type {
  CohortRetentionResponse,
  CorrelationResponse,
  DistributionResponse,
  FunnelResponse,
  RawSchemaResponse,
  TimeSeriesResponse,
} from "@data-analyst-lab/shared";

import { apiClient } from "@/lib/api-client";

/** Column names via plain DuckDB introspection — works even for datasets with no
 * DatasetProfile (e.g. SqlTable-only databases like "ecommerce"/"saas-product"). */
export function useDatasetRawSchema(idOrSlug: string | undefined, table: string | undefined) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "raw-schema", table],
    queryFn: () => {
      const params = table ? `?table=${encodeURIComponent(table)}` : "";
      return apiClient.get<RawSchemaResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/analysis/raw-schema${params}`);
    },
    enabled: Boolean(idOrSlug),
    staleTime: 60 * 1000,
  });
}

/** Pearson/Spearman correlation matrix for a set of numeric columns. */
export function useDatasetCorrelation(
  idOrSlug: string | undefined,
  table: string | undefined,
  columns: string[],
  method: "pearson" | "spearman",
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "correlation", table, columns, method],
    queryFn: () => {
      const params = new URLSearchParams({ columns: columns.join(","), method });
      if (table) params.set("table", table);
      return apiClient.get<CorrelationResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/analysis/correlation?${params}`);
    },
    enabled: Boolean(idOrSlug) && columns.length >= 2 && enabled,
    staleTime: 30 * 1000,
  });
}

/** Histogram + summary stats for one numeric column, with a configurable bin count. */
export function useDatasetDistribution(
  idOrSlug: string | undefined,
  table: string | undefined,
  column: string | undefined,
  bins: number,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "distribution", table, column, bins],
    queryFn: () => {
      const params = new URLSearchParams({ column: column!, bins: String(bins) });
      if (table) params.set("table", table);
      return apiClient.get<DistributionResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/analysis/distribution?${params}`);
    },
    enabled: Boolean(idOrSlug) && Boolean(column) && enabled,
    staleTime: 30 * 1000,
  });
}

/** A metric aggregated over time at a chosen granularity, with a rolling average overlay. */
export function useDatasetTimeSeries(
  idOrSlug: string | undefined,
  table: string | undefined,
  dateColumn: string | undefined,
  metricColumn: string | undefined,
  aggregation: string,
  granularity: string,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "timeseries", table, dateColumn, metricColumn, aggregation, granularity],
    queryFn: () => {
      const params = new URLSearchParams({
        date_column: dateColumn!,
        metric_column: metricColumn!,
        aggregation,
        granularity,
      });
      if (table) params.set("table", table);
      return apiClient.get<TimeSeriesResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/analysis/timeseries?${params}`);
    },
    enabled: Boolean(idOrSlug) && Boolean(dateColumn) && Boolean(metricColumn) && enabled,
    staleTime: 30 * 1000,
  });
}

/** Step-by-step conversion/drop-off for a sequence of event names (spec section 36). */
export function useDatasetFunnel(
  idOrSlug: string | undefined,
  table: string | undefined,
  userCol: string | undefined,
  eventCol: string | undefined,
  steps: string[],
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["datasets", "detail", idOrSlug, "funnel", table, userCol, eventCol, steps],
    queryFn: () => {
      const params = new URLSearchParams({ user_col: userCol!, event_col: eventCol!, steps: steps.join(",") });
      if (table) params.set("table", table);
      return apiClient.get<FunnelResponse>(`/datasets/${encodeURIComponent(idOrSlug!)}/analysis/funnel?${params}`);
    },
    enabled: Boolean(idOrSlug) && Boolean(userCol) && Boolean(eventCol) && steps.length >= 2 && enabled,
    staleTime: 30 * 1000,
  });
}

/** A cohort × period retention matrix (spec section 37). */
export function useDatasetCohortRetention(
  idOrSlug: string | undefined,
  table: string | undefined,
  userCol: string | undefined,
  cohortDateCol: string | undefined,
  activityDateCol: string | undefined,
  granularity: string,
  periods: number,
  enabled: boolean,
) {
  return useQuery({
    queryKey: [
      "datasets",
      "detail",
      idOrSlug,
      "cohort-retention",
      table,
      userCol,
      cohortDateCol,
      activityDateCol,
      granularity,
      periods,
    ],
    queryFn: () => {
      const params = new URLSearchParams({
        user_col: userCol!,
        cohort_date_col: cohortDateCol!,
        activity_date_col: activityDateCol!,
        granularity,
        periods: String(periods),
      });
      if (table) params.set("table", table);
      return apiClient.get<CohortRetentionResponse>(
        `/datasets/${encodeURIComponent(idOrSlug!)}/analysis/cohort-retention?${params}`,
      );
    },
    enabled:
      Boolean(idOrSlug) && Boolean(userCol) && Boolean(cohortDateCol) && Boolean(activityDateCol) && enabled,
    staleTime: 30 * 1000,
  });
}
