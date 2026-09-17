"use client";

import { useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Download, Upload } from "lucide-react";
import type { BackupBundle } from "@data-analyst-lab/shared";

import { useToast } from "@/components/shared/toast-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useCreateBackup, usePreviewRestore, useRestore } from "@/features/platform/use-platform";

/** Mirrors the existing downloadText helper (career-analytics-page.tsx) rather than inventing a new pattern. */
function downloadText(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Backup / Restore (Phase 12, spec sections 20-21). Backup is a plain
 * download of GET /platform/backup. Restore always previews first
 * (POST /platform/restore/preview) and shows the manifest + any
 * compatibility issues before requiring an explicit confirming checkbox —
 * the actual POST /platform/restore call always sends confirm: true only
 * once the user has ticked it, never by default.
 */
export function BackupRestoreCard() {
  const { toast } = useToast();
  const createBackup = useCreateBackup();
  const previewRestore = usePreviewRestore();
  const restore = useRestore();

  const [pendingBundle, setPendingBundle] = useState<BackupBundle | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleDownloadBackup() {
    createBackup.mutate(undefined, {
      onSuccess: (bundle) => {
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        downloadText(`data-analyst-lab-backup-${timestamp}.json`, JSON.stringify(bundle, null, 2), "application/json");
        toast({ title: "Backup saved", description: "The download should appear in your browser's downloads.", variant: "success" });
      },
      onError: () => {
        toast({ title: "Backup failed", description: "We couldn't reach the API to create a backup.", variant: "error" });
      },
    });
  }

  async function handleFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // allow re-selecting the same file later
    if (!file) return;

    setFileError(null);
    setConfirmed(false);
    setPendingBundle(null);
    previewRestore.reset();

    let parsed: BackupBundle;
    try {
      const text = await file.text();
      parsed = JSON.parse(text) as BackupBundle;
    } catch {
      setFileError("That file isn't valid JSON — choose a backup file created by \"Download Backup\".");
      return;
    }

    setPendingBundle(parsed);
    previewRestore.mutate(parsed, {
      onError: () => {
        toast({ title: "Couldn't preview backup", description: "The file may not be a valid backup bundle.", variant: "error" });
      },
    });
  }

  function handleRestore() {
    if (!pendingBundle || !confirmed) return;
    restore.mutate(
      { bundle: pendingBundle, confirm: true },
      {
        onSuccess: (result) => {
          const totalRows = Object.values(result.restored).reduce((sum, n) => sum + n, 0);
          toast({
            title: "Restore complete",
            description: `Restored ${totalRows} row${totalRows === 1 ? "" : "s"} across ${Object.keys(result.restored).length} table(s).`,
            variant: "success",
          });
          setPendingBundle(null);
          setConfirmed(false);
          previewRestore.reset();
        },
        onError: () => {
          toast({ title: "Restore failed", description: "We couldn't reach the API to restore this backup.", variant: "error" });
        },
      },
    );
  }

  const preview = previewRestore.data;

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle>Backup &amp; Restore</CardTitle>
        <CardDescription>
          Export everything you own to a local JSON file, or restore from one — never includes secrets like API
          keys.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        <div>
          <p className="mb-2 text-sm font-medium text-foreground">Download Backup</p>
          <Button onClick={handleDownloadBackup} disabled={createBackup.isPending} variant="outline">
            <Download className="size-4" aria-hidden="true" />
            {createBackup.isPending ? "Preparing…" : "Download Backup"}
          </Button>
        </div>

        <div className="flex flex-col gap-3 border-t border-border pt-4">
          <p className="text-sm font-medium text-foreground">Restore from Backup</p>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json"
            onChange={(event) => void handleFileSelected(event)}
            className="hidden"
            aria-label="Choose a backup file"
          />
          <Button
            variant="outline"
            className="self-start"
            onClick={() => fileInputRef.current?.click()}
            disabled={previewRestore.isPending}
          >
            <Upload className="size-4" aria-hidden="true" />
            {previewRestore.isPending ? "Reading…" : "Choose Backup File"}
          </Button>

          {fileError ? (
            <p className="flex items-center gap-1.5 text-xs text-destructive">
              <AlertTriangle className="size-3.5 shrink-0" aria-hidden="true" />
              {fileError}
            </p>
          ) : null}

          {preview ? (
            <div className="flex flex-col gap-3 rounded-md border border-border p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={preview.compatible ? "success" : "destructive"}>
                  {preview.compatible ? "Compatible" : "Incompatible"}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  Created {new Date(preview.manifest.created_at).toLocaleString()} · app v{preview.manifest.app_version}
                </span>
              </div>

              <div className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">Rows to restore: </span>
                {Object.entries(preview.manifest.counts).length === 0
                  ? "none"
                  : Object.entries(preview.manifest.counts)
                      .map(([table, count]) => `${table} (${count})`)
                      .join(", ")}
              </div>

              {preview.issues.length > 0 ? (
                <ul className="flex flex-col gap-1">
                  {preview.issues.map((issue, index) => (
                    <li key={index} className="flex items-start gap-1.5 text-xs text-warning">
                      <AlertTriangle className="mt-0.5 size-3 shrink-0" aria-hidden="true" />
                      {issue}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="flex items-center gap-1.5 text-xs text-success">
                  <CheckCircle2 className="size-3 shrink-0" aria-hidden="true" />
                  No compatibility issues found.
                </p>
              )}

              <label className="flex items-start gap-2 text-xs text-foreground">
                <input
                  type="checkbox"
                  className="mt-0.5 size-4"
                  checked={confirmed}
                  onChange={(event) => setConfirmed(event.target.checked)}
                />
                I understand this will add back anything in this backup that&apos;s missing from my
                current data, without changing or removing anything that&apos;s already here.
              </label>

              <Button
                variant="destructive"
                size="sm"
                className="self-start"
                disabled={!confirmed || restore.isPending}
                onClick={handleRestore}
              >
                {restore.isPending ? "Restoring…" : "Yes, Restore"}
              </Button>
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
