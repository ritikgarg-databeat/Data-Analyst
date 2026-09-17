"use client";

import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useSqlTablePreview } from "@/features/sql/use-sql-table-preview";

import { ResultsGrid } from "./results-grid";

interface TablePreviewPanelProps {
  database: string;
  engine: string;
  table: string | null;
  onOpenChange: (open: boolean) => void;
}

/** Slide-over panel showing a table's sample rows — reuses ResultsGrid rather than a second grid implementation. */
export function TablePreviewPanel({ database, engine, table, onOpenChange }: TablePreviewPanelProps) {
  const open = table !== null;
  const previewQuery = useSqlTablePreview(database, table ?? "", engine, { enabled: open });

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full max-w-3xl sm:max-w-3xl">
        <SheetHeader>
          <SheetTitle>{table ?? "Table preview"}</SheetTitle>
          <SheetDescription>
            {previewQuery.data
              ? `Sample of ${previewQuery.data.sample_row_count.toLocaleString()} rows out of ${previewQuery.data.row_count.toLocaleString()} total.`
              : "A small sample of this table's rows."}
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-auto px-4 pb-4">
          {previewQuery.isLoading ? (
            <LoadingState count={1} itemClassName="h-64" />
          ) : previewQuery.isError ? (
            <ErrorState
              title="Unable to load preview"
              message="We couldn't fetch sample rows for this table."
              retry={() => void previewQuery.refetch()}
            />
          ) : previewQuery.data ? (
            <ResultsGrid
              columns={previewQuery.data.columns}
              rows={previewQuery.data.rows}
              rowCount={previewQuery.data.row_count}
            />
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  );
}
