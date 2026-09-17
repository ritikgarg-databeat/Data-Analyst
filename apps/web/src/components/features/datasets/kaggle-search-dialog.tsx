"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Download, Search, Star } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { Input } from "@/components/ui/input";
import { LoadingState } from "@/components/shared/loading-state";
import { useKaggleFiles, useKaggleImport, useKaggleSearch, useKaggleStatus } from "@/features/kaggle/use-kaggle";

const numberFormatter = new Intl.NumberFormat("en-US");

function formatBytes(bytes: number | null): string {
  if (bytes === null) return "—";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface KaggleSearchDialogProps {
  trigger?: React.ReactNode;
}

/**
 * Kaggle search -> inspect -> select files -> import (sections 8-10 of the
 * Phase 5 spec). Renders a clear "not configured" state with setup
 * instructions when KAGGLE_USERNAME/KAGGLE_KEY aren't set — the rest of the
 * Dataset Hub works normally either way.
 */
export function KaggleSearchDialog({ trigger }: KaggleSearchDialogProps) {
  const router = useRouter();
  const statusQuery = useKaggleStatus();

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [selectedRef, setSelectedRef] = useState<string | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [importName, setImportName] = useState("");

  const searchQuery = useKaggleSearch(submittedQuery, 1);
  const filesQuery = useKaggleFiles(selectedRef);
  const importMutation = useKaggleImport(selectedRef);

  function reset() {
    setQuery("");
    setSubmittedQuery("");
    setSelectedRef(null);
    setSelectedFiles(new Set());
    setImportName("");
    importMutation.reset();
  }

  function toggleFile(name: string) {
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  function handleImport() {
    if (selectedFiles.size === 0 || !importName.trim()) return;
    importMutation.mutate(
      { name: importName.trim(), files: Array.from(selectedFiles) },
      {
        onSuccess: (dataset) => {
          setOpen(false);
          reset();
          router.push(`/datasets/${dataset.slug}`);
        },
      },
    );
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);
        if (!next) reset();
      }}
    >
      <DialogTrigger asChild>
        {trigger ?? (
          <Button variant="outline">
            <Search className="size-4" aria-hidden="true" />
            Search Kaggle
          </Button>
        )}
      </DialogTrigger>
      <DialogContent size="xl">
        <DialogHeader>
          <DialogTitle>Kaggle Datasets</DialogTitle>
          <DialogDescription>
            Search Kaggle&apos;s public dataset catalog via the official Kaggle API, inspect its files, and
            import only what you choose.
          </DialogDescription>
        </DialogHeader>

        {statusQuery.isLoading ? (
          <LoadingState count={1} itemClassName="h-24" />
        ) : statusQuery.isError ? (
          <ErrorState
            title="Unable to check Kaggle status"
            message="We couldn't reach the API to check whether Kaggle is configured."
            retry={() => void statusQuery.refetch()}
          />
        ) : !statusQuery.data?.configured ? (
          <EmptyState
            icon={Search}
            title="Kaggle integration is not configured"
            description={
              statusQuery.data?.setup_instructions ??
              "Set KAGGLE_USERNAME and KAGGLE_KEY in your .env file to enable Kaggle search and import."
            }
          />
        ) : selectedRef ? (
          <div className="flex flex-col gap-4">
            <button
              type="button"
              onClick={() => {
                setSelectedRef(null);
                setSelectedFiles(new Set());
              }}
              className="w-fit text-sm text-primary hover:underline"
            >
              ← Back to results
            </button>

            <div>
              <h3 className="text-sm font-semibold text-foreground">{selectedRef}</h3>
              <p className="text-xs text-muted-foreground">Select the file(s) you want to import.</p>
            </div>

            {filesQuery.isLoading ? (
              <LoadingState count={3} itemClassName="h-10" />
            ) : filesQuery.isError ? (
              <ErrorState message="Couldn't load this dataset's files." retry={() => void filesQuery.refetch()} />
            ) : (
              <ul className="flex flex-col gap-1.5">
                {(filesQuery.data?.files ?? []).map((file) => (
                  <li key={file.name}>
                    <label className="flex cursor-pointer items-center gap-2 rounded-md border border-border px-3 py-2 text-sm hover:bg-accent/40">
                      <input
                        type="checkbox"
                        checked={selectedFiles.has(file.name)}
                        onChange={() => toggleFile(file.name)}
                        className="size-4"
                      />
                      <span className="flex-1 truncate">{file.name}</span>
                      <span className="text-xs text-muted-foreground">{formatBytes(file.size_bytes)}</span>
                    </label>
                  </li>
                ))}
              </ul>
            )}

            <div className="flex flex-col gap-1">
              <label htmlFor="kaggle-import-name" className="text-sm font-medium">
                Dataset name
              </label>
              <Input
                id="kaggle-import-name"
                value={importName}
                onChange={(event) => setImportName(event.target.value)}
                placeholder="Customer Churn Dataset"
              />
            </div>

            {importMutation.isError ? (
              <p role="alert" className="text-sm text-destructive">
                {importMutation.error instanceof Error ? importMutation.error.message : "Import failed."}
              </p>
            ) : null}

            <DialogFooter>
              <Button
                onClick={handleImport}
                disabled={selectedFiles.size === 0 || !importName.trim() || importMutation.isPending}
              >
                <Download className="size-4" aria-hidden="true" />
                {importMutation.isPending
                  ? "Importing…"
                  : `Import ${selectedFiles.size || ""} file${selectedFiles.size === 1 ? "" : "s"}`.trim()}
              </Button>
            </DialogFooter>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <form
              className="flex gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                setSubmittedQuery(query.trim());
              }}
            >
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder='Search Kaggle, e.g. "customer churn"'
                aria-label="Search Kaggle datasets"
              />
              <Button type="submit" disabled={!query.trim()}>
                <Search className="size-4" aria-hidden="true" />
                Search
              </Button>
            </form>

            {searchQuery.isLoading ? (
              <LoadingState count={3} itemClassName="h-20" />
            ) : searchQuery.isError ? (
              <ErrorState message="Kaggle search failed." retry={() => void searchQuery.refetch()} />
            ) : searchQuery.data && searchQuery.data.results.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No datasets found for “{submittedQuery}”.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {(searchQuery.data?.results ?? []).map((result) => (
                  <li key={result.ref} className="rounded-lg border border-border p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-foreground">{result.title}</p>
                        {result.subtitle ? (
                          <p className="text-xs text-muted-foreground">{result.subtitle}</p>
                        ) : null}
                      </div>
                      {result.usability_rating !== null ? (
                        <Badge variant="outline" className="gap-1 shrink-0">
                          <Star className="size-3" aria-hidden="true" />
                          {(result.usability_rating * 5).toFixed(1)}
                        </Badge>
                      ) : null}
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>{formatBytes(result.size_bytes)}</span>
                      {result.download_count !== null ? (
                        <span>{numberFormatter.format(result.download_count)} downloads</span>
                      ) : null}
                      {result.license_name ? <span>{result.license_name}</span> : null}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-2"
                      onClick={() => {
                        setSelectedRef(result.ref);
                        setImportName(result.title);
                      }}
                    >
                      Inspect
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
