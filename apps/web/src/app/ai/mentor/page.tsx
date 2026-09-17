"use client";

import { Bot } from "lucide-react";

import { AIMentorChat } from "@/components/features/ai/ai-mentor-panel";
import { PageHeader } from "@/components/shared/page-header";

/**
 * Full-page AI Mentor (Phase 12) — reuses the same chat component/hooks as
 * the floating Sheet launcher (AIMentorPanel) rather than a second
 * implementation; only the surrounding chrome (page header + a fixed-height
 * container instead of a slide-in sheet) differs.
 */
export default function AIMentorPage() {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="AI Mentor"
        subtitle="Ask anything about SQL, Python, statistics, or a specific lesson or case — with the same context-aware mentor available everywhere else in the app."
        action={<Bot className="size-6 text-muted-foreground" aria-hidden="true" />}
      />
      <p className="rounded-md border border-border bg-muted p-2 text-xs text-muted-foreground">
        This interaction may send selected learning/code/data context to the configured AI provider.
      </p>
      <AIMentorChat className="h-[70vh] min-h-[420px]" />
    </div>
  );
}
