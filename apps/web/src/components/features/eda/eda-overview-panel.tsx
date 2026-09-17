import type { EdaOverview } from "@data-analyst-lab/shared";

import { Badge } from "@/components/ui/badge";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <p className="mb-3 text-sm font-semibold text-foreground">{title}</p>
      {children}
    </div>
  );
}

/** Renders a "Generate EDA Overview" result (section 20 of the Phase 5 spec) — deterministic, not AI. */
export function EdaOverviewPanel({ overview }: { overview: EdaOverview }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Section title="Dataset overview">
        <dl className="grid grid-cols-3 gap-2 text-sm">
          <div>
            <dt className="text-xs text-muted-foreground">Rows</dt>
            <dd className="font-semibold text-foreground">{overview.row_count.toLocaleString()}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Columns</dt>
            <dd className="font-semibold text-foreground">{overview.column_count}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Duplicates</dt>
            <dd className="font-semibold text-foreground">{overview.duplicate_row_count.toLocaleString()}</dd>
          </div>
        </dl>
      </Section>

      <Section title="Missingness">
        {overview.missingness.length === 0 ? (
          <p className="text-sm text-muted-foreground">No missing values found.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {overview.missingness.map((m) => (
              <li key={m.column} className="flex items-center gap-2 text-sm">
                <span className="w-28 truncate">{m.column}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                  <div className="h-full bg-warning" style={{ width: `${Math.min(m.null_percentage, 100)}%` }} />
                </div>
                <span className="w-12 shrink-0 text-right tabular-nums text-muted-foreground">
                  {m.null_percentage.toFixed(1)}%
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Numeric distributions">
        {overview.distributions.length === 0 ? (
          <p className="text-sm text-muted-foreground">No numeric columns.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {overview.distributions.map((d) => (
              <li key={d.column} className="text-sm">
                <span className="font-medium text-foreground">{d.column}</span>{" "}
                <span className="text-muted-foreground">
                  mean {d.mean?.toFixed(1) ?? "—"} · median {d.median?.toFixed(1) ?? "—"} · std{" "}
                  {d.std_dev?.toFixed(1) ?? "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Categorical summaries">
        {overview.categorical_summaries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No categorical columns.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {overview.categorical_summaries.map((c) => (
              <li key={c.column} className="text-sm">
                <span className="font-medium text-foreground">{c.column}</span>{" "}
                <span className="text-muted-foreground">
                  top: {c.top_values.slice(0, 3).map((v) => v.value).join(", ") || "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Correlations">
        {overview.correlations.length === 0 ? (
          <p className="text-sm text-muted-foreground">No notable correlations (|r| ≥ 0.3) found.</p>
        ) : (
          <>
            <ul className="flex flex-col gap-1.5">
              {overview.correlations.map((c) => (
                <li key={`${c.column_a}-${c.column_b}`} className="flex items-center justify-between text-sm">
                  <span>
                    {c.column_a} ↔ {c.column_b}
                  </span>
                  <Badge variant={Math.abs(c.correlation) >= 0.7 ? "default" : "outline"}>
                    {c.correlation.toFixed(2)}
                  </Badge>
                </li>
              ))}
            </ul>
            <p className="mt-2 text-xs text-muted-foreground">Correlation does not imply causation.</p>
          </>
        )}
      </Section>

      <Section title="Date trends">
        {overview.date_trends.length === 0 ? (
          <p className="text-sm text-muted-foreground">No datetime columns.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {overview.date_trends.map((d) => (
              <li key={d.column} className="text-sm">
                <span className="font-medium text-foreground">{d.column}</span>{" "}
                <span className="text-muted-foreground">
                  {d.min_date} → {d.max_date}
                  {d.missing_calendar_days ? ` · ${d.missing_calendar_days} missing calendar day(s)` : ""}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Potential outliers">
        {overview.outliers.length === 0 ? (
          <p className="text-sm text-muted-foreground">No outliers flagged.</p>
        ) : (
          <ul className="flex flex-col gap-1.5">
            {overview.outliers.map((o) => (
              <li key={o.column} className="text-sm">
                <span className="font-medium text-foreground">{o.column}</span>{" "}
                <span className="text-muted-foreground">
                  {o.outlier_count} potential outlier(s) ({o.method})
                </span>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          Outliers may be legitimate business observations, not errors — use judgment.
        </p>
      </Section>
    </div>
  );
}
