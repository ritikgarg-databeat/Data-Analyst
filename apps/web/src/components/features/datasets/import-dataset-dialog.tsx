"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileSpreadsheet, Upload, X } from "lucide-react";
import type { DifficultyLevel } from "@data-analyst-lab/shared";

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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useImportDataset } from "@/features/datasets/use-datasets";

const ACCEPTED_EXTENSIONS = [".csv", ".parquet", ".json", ".xlsx"];

function formatBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface ImportDatasetDialogProps {
  trigger?: React.ReactNode;
}

/**
 * Local dataset import (section 5/6/7 of the Phase 5 spec): choose one file,
 * or several at once to import as a related "collection" (one table per
 * file). Files are handed straight to `postForm` as native `File` objects —
 * never read into a JS string first, so large files stay memory-safe.
 */
export function ImportDatasetDialog({ trigger }: ImportDatasetDialogProps) {
  const router = useRouter();
  const importMutation = useImportDataset();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [open, setOpen] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [businessDomain, setBusinessDomain] = useState("");
  const [difficulty, setDifficulty] = useState<DifficultyLevel>("BEGINNER");
  const [tags, setTags] = useState("");
  const [dragActive, setDragActive] = useState(false);

  function reset() {
    setFiles([]);
    setName("");
    setDescription("");
    setBusinessDomain("");
    setDifficulty("BEGINNER");
    setTags("");
    importMutation.reset();
  }

  function addFiles(list: FileList | null) {
    if (!list) return;
    const next = Array.from(list);
    setFiles((prev) => [...prev, ...next]);
    if (!name && next[0]) {
      setName(next[0].name.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " "));
    }
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  function handleSubmit() {
    if (files.length === 0 || !name.trim()) return;
    importMutation.mutate(
      {
        files,
        form: {
          name: name.trim(),
          description: description.trim() || undefined,
          business_domain: businessDomain.trim() || undefined,
          difficulty,
          tags: tags
            .split(",")
            .map((t) => t.trim())
            .filter(Boolean),
        },
      },
      {
        onSuccess: (dataset) => {
          setOpen(false);
          reset();
          router.push(`/datasets/${dataset.slug}`);
        },
      },
    );
  }

  const totalSize = files.reduce((sum, f) => sum + f.size, 0);
  const canSubmit = files.length > 0 && name.trim().length > 0 && !importMutation.isPending;

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
          <Button>
            <Upload className="size-4" aria-hidden="true" />
            Import Dataset
          </Button>
        )}
      </DialogTrigger>
      <DialogContent size="lg">
        <DialogHeader>
          <DialogTitle>Import Dataset</DialogTitle>
          <DialogDescription>
            Upload a CSV, Parquet, JSON, or Excel file — or select several related files at once to
            import them as one dataset collection (e.g. customers.csv + orders.csv).
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <div
            className={`flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors ${
              dragActive ? "border-primary bg-accent/40" : "border-border"
            }`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(event) => {
              event.preventDefault();
              setDragActive(false);
              addFiles(event.dataTransfer.files);
            }}
          >
            <Upload className="size-6 text-muted-foreground" aria-hidden="true" />
            <p className="text-sm text-muted-foreground">
              Drag files here, or{" "}
              <button
                type="button"
                className="font-medium text-primary hover:underline"
                onClick={() => fileInputRef.current?.click()}
              >
                choose files
              </button>
            </p>
            <p className="text-xs text-muted-foreground">Supported: {ACCEPTED_EXTENSIONS.join(", ")}</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={ACCEPTED_EXTENSIONS.join(",")}
              aria-label="Choose files to import"
              className="sr-only"
              onChange={(event) => addFiles(event.target.files)}
            />
          </div>

          {files.length > 0 ? (
            <ul className="flex flex-col gap-1.5">
              {files.map((file, index) => (
                <li
                  key={`${file.name}-${index}`}
                  className="flex items-center justify-between gap-2 rounded-md border border-border px-3 py-1.5 text-sm"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <FileSpreadsheet className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                    <span className="truncate">{file.name}</span>
                    <span className="shrink-0 text-xs text-muted-foreground">{formatBytes(file.size)}</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="shrink-0 rounded p-0.5 text-muted-foreground hover:text-foreground"
                    aria-label={`Remove ${file.name}`}
                  >
                    <X className="size-3.5" />
                  </button>
                </li>
              ))}
              {files.length > 1 ? (
                <li className="text-xs text-muted-foreground">
                  {files.length} files · {formatBytes(totalSize)} total — will be imported as one collection
                </li>
              ) : null}
            </ul>
          ) : null}

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1 sm:col-span-2">
              <Label htmlFor="import-name">Dataset name</Label>
              <Input
                id="import-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="E-commerce Orders"
              />
            </div>
            <div className="flex flex-col gap-1 sm:col-span-2">
              <Label htmlFor="import-description">Description</Label>
              <Textarea
                id="import-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="What is this dataset, and where did it come from?"
                className="min-h-16"
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="import-domain">Domain</Label>
              <Input
                id="import-domain"
                value={businessDomain}
                onChange={(event) => setBusinessDomain(event.target.value)}
                placeholder="E-commerce"
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="import-difficulty">Difficulty</Label>
              <Select
                id="import-difficulty"
                value={difficulty}
                onChange={(event) => setDifficulty(event.target.value as DifficultyLevel)}
              >
                <option value="BEGINNER">Beginner</option>
                <option value="INTERMEDIATE">Intermediate</option>
                <option value="ADVANCED">Advanced</option>
              </Select>
            </div>
            <div className="flex flex-col gap-1 sm:col-span-2">
              <Label htmlFor="import-tags">Tags</Label>
              <Input
                id="import-tags"
                value={tags}
                onChange={(event) => setTags(event.target.value)}
                placeholder="e-commerce, beginner, real-world"
              />
              <p className="text-xs text-muted-foreground">Comma-separated.</p>
            </div>
          </div>

          {importMutation.isError ? (
            <p role="alert" className="text-sm text-destructive">
              {importMutation.error instanceof Error ? importMutation.error.message : "Import failed."}
            </p>
          ) : null}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {importMutation.isPending ? "Importing…" : "Import Dataset"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
