"use client";

import { useMemo, useState } from "react";
import { Database, Search } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingState } from "@/components/shared/loading-state";
import { Input } from "@/components/ui/input";
import { useDatasets } from "@/features/datasets/use-datasets";
import { cn } from "@/lib/utils";

import { DatasetCard } from "./dataset-card";
import { ImportDatasetDialog } from "./import-dataset-dialog";
import { KaggleSearchDialog } from "./kaggle-search-dialog";

const DOMAIN_CHIPS = ["All", "Business", "Product", "Finance", "Marketing", "Healthcare", "E-commerce", "Operations"];

export function DatasetHub() {
  const [search, setSearch] = useState("");
  const [domainChip, setDomainChip] = useState("All");
  const datasetsQuery = useDatasets(search.trim() ? { q: search.trim() } : undefined);

  const filtered = useMemo(() => {
    const datasets = datasetsQuery.data ?? [];
    if (domainChip === "All") return datasets;
    return datasets.filter((d) => (d.business_domain ?? "").toLowerCase() === domainChip.toLowerCase());
  }, [datasetsQuery.data, domainChip]);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full max-w-sm">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search datasets, columns, tags…"
            className="pl-9"
            aria-label="Search datasets"
          />
        </div>
        <div className="flex gap-2">
          <KaggleSearchDialog />
          <ImportDatasetDialog />
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5" role="tablist" aria-label="Filter by business domain">
        {DOMAIN_CHIPS.map((chip) => (
          <button
            key={chip}
            type="button"
            role="tab"
            aria-selected={domainChip === chip}
            onClick={() => setDomainChip(chip)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              domainChip === chip
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-muted-foreground hover:bg-accent/60 hover:text-foreground",
            )}
          >
            {chip}
          </button>
        ))}
      </div>

      {datasetsQuery.isLoading ? (
        <LoadingState count={6} className="grid-cols-1 sm:grid-cols-2 lg:grid-cols-3" itemClassName="h-48" />
      ) : datasetsQuery.isError ? (
        <ErrorState
          title="Unable to load datasets"
          message="We couldn't reach the API to load the dataset catalog."
          retry={() => void datasetsQuery.refetch()}
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={Database}
          title={search || domainChip !== "All" ? "No matching datasets" : "No datasets yet"}
          description={
            search || domainChip !== "All"
              ? "Try a different search term or domain filter."
              : "Import a local file, or search Kaggle, to add your first dataset."
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((dataset) => (
            <DatasetCard key={dataset.id} dataset={dataset} />
          ))}
        </div>
      )}
    </div>
  );
}
