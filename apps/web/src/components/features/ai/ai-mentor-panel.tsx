"use client";

import { useState } from "react";
import { Bot, Send } from "lucide-react";
import type { AIContextType } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { useAIConversation, useAISettings, useAskMentor } from "@/features/ai/use-ai";

const CONTEXT_OPTIONS: { value: AIContextType; label: string }[] = [
  { value: "sql", label: "SQL Lab" },
  { value: "python", label: "Python Lab" },
  { value: "lesson", label: "Current Lesson" },
  { value: "case", label: "Current Case" },
  { value: "general", label: "General" },
];

interface AIMentorChatProps {
  className?: string;
}

/**
 * The AI Mentor's actual chat UI (context picker, message list, composer) —
 * extracted from AIMentorPanel so it can be reused both as the floating
 * Sheet panel (every route, via AIMentorLauncher) and inline as the full
 * /ai/mentor page (Phase 12), without duplicating the chat logic.
 */
export function AIMentorChat({ className }: AIMentorChatProps) {
  const [contextType, setContextType] = useState<AIContextType>("general");
  const [contextId, setContextId] = useState("");
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  const settingsQuery = useAISettings();
  const conversationQuery = useAIConversation(conversationId);
  const askMentor = useAskMentor();

  function handleAsk() {
    if (!message.trim()) return;
    askMentor.mutate(
      {
        message,
        context_type: contextType,
        context_id: contextId.trim() || null,
        conversation_id: conversationId ?? null,
      },
      {
        onSuccess: (response) => {
          setConversationId(response.conversation_id);
          setMessage("");
        },
      },
    );
  }

  const messages = conversationQuery.data?.messages ?? [];

  return (
    <div className={cn("flex flex-col gap-4", className)}>
      {settingsQuery.data && !settingsQuery.data.enabled ? (
        <p className="rounded-md border border-border bg-muted p-2 text-xs text-muted-foreground">
          AI is disabled in your AI Settings. Enable it on the Settings page to use the mentor.
        </p>
      ) : settingsQuery.data && settingsQuery.data.effective_provider === "local" ? (
        <p className="rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          No AI provider is configured yet — set AI_PROVIDER and an API key (see .env.example) for real AI
          responses. Responses right now are a local, no-network placeholder.
        </p>
      ) : null}

      <div className="flex items-center gap-2">
        <label className="shrink-0 text-xs font-medium text-muted-foreground" htmlFor="mentor-context">
          Context
        </label>
        <Select
          id="mentor-context"
          value={contextType}
          onChange={(event) => {
            setContextType(event.target.value as AIContextType);
            setContextId("");
            setConversationId(undefined);
          }}
          className="w-40 shrink-0"
        >
          {CONTEXT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </Select>
        {contextType === "case" || contextType === "lesson" ? (
          <input
            className="h-9 min-w-0 flex-1 rounded-md border border-input bg-transparent px-2 text-sm shadow-sm outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
            placeholder={contextType === "case" ? "Case attempt ID" : "Lesson slug"}
            value={contextId}
            onChange={(event) => setContextId(event.target.value)}
          />
        ) : null}
      </div>

      <div className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-md border border-border p-3">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">What are you working on? Ask anything.</p>
        ) : (
          messages.map((message_) => (
            <div
              key={message_.id}
              className={
                message_.role === "USER"
                  ? "max-w-[85%] self-end rounded-lg bg-primary/10 px-3 py-2 text-sm text-foreground"
                  : "max-w-[85%] self-start rounded-lg bg-muted px-3 py-2 text-sm whitespace-pre-wrap text-foreground"
              }
            >
              {message_.content}
            </div>
          ))
        )}
      </div>

      <div className="flex gap-2">
        <Textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask anything..."
          rows={2}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              handleAsk();
            }
          }}
        />
        <Button onClick={handleAsk} disabled={askMentor.isPending || !message.trim()} size="icon" aria-label="Ask">
          <Send className="size-4" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}

/**
 * AI Mentor (spec section 6) — accessible globally via AIMentorLauncher in
 * app-shell.tsx. A manual context picker (matching the spec's own mockup)
 * rather than automatic route detection: the learner tells the mentor what
 * they're working on, and — for lesson/case — which one, since a global
 * launcher has no reliable way to infer "the current exercise" on its own.
 */
export function AIMentorPanel({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full max-w-md flex-col gap-4 sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Bot className="size-5" aria-hidden="true" />
            AI Data Analyst Mentor
          </SheetTitle>
          <SheetDescription>
            This interaction may send selected learning/code/data context to the configured AI provider.
          </SheetDescription>
        </SheetHeader>

        <AIMentorChat className="flex-1" />
      </SheetContent>
    </Sheet>
  );
}
