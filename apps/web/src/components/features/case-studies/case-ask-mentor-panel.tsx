"use client";

import { useState } from "react";
import { Bot, Send } from "lucide-react";
import type { AICaseCoachingMode } from "@data-analyst-lab/shared";

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
import { useAIConversation, useCaseCoach, useCaseInterviewerTurn } from "@/features/ai/use-ai";

const MODE_OPTIONS: { value: AICaseCoachingMode; label: string; hint: string }[] = [
  { value: "GUIDED", label: "Guided", hint: "Strong hints when you're stuck." },
  { value: "STANDARD", label: "Standard", hint: "Questions and moderate guidance." },
  { value: "INTERVIEW", label: "Mock Interview", hint: "The AI plays the stakeholder — ask it clarifying questions." },
  { value: "STRICT", label: "Strict", hint: "Minimal assistance — for real practice." },
];

/**
 * Ask Mentor inside the Case Workspace (spec sections 24-28) — 4 coaching
 * modes; "Mock Interview" routes to the dedicated AI Case Interviewer
 * endpoint (progressive, gated reveal) instead of the general Case Coach,
 * while sharing the same chat UI/conversation thread.
 */
export function CaseAskMentorPanel({
  open,
  onOpenChange,
  attemptId,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  attemptId: string;
}) {
  const [coachingMode, setCoachingMode] = useState<AICaseCoachingMode>("STANDARD");
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  const conversationQuery = useAIConversation(conversationId);
  const caseCoach = useCaseCoach(attemptId);
  const caseInterviewer = useCaseInterviewerTurn(attemptId);
  const isInterviewMode = coachingMode === "INTERVIEW";
  const activeMutation = isInterviewMode ? caseInterviewer : caseCoach;

  function handleAsk() {
    if (!message.trim()) return;
    const onSuccess = (response: { conversation_id: string }) => {
      setConversationId(response.conversation_id);
      setMessage("");
    };
    if (isInterviewMode) {
      caseInterviewer.mutate({ message, conversation_id: conversationId ?? null }, { onSuccess });
    } else {
      caseCoach.mutate({ message, coaching_mode: coachingMode, conversation_id: conversationId ?? null }, { onSuccess });
    }
  }

  const messages = conversationQuery.data?.messages ?? [];

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full max-w-md flex-col gap-4 sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Bot className="size-5" aria-hidden="true" />
            Ask Mentor
          </SheetTitle>
          <SheetDescription>
            This sends the case&apos;s public details and your own work so far to the configured AI provider.
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-muted-foreground" htmlFor="case-coaching-mode">
            Coaching mode
          </label>
          <Select
            id="case-coaching-mode"
            value={coachingMode}
            onChange={(event) => {
              setCoachingMode(event.target.value as AICaseCoachingMode);
              setConversationId(undefined);
            }}
          >
            {MODE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <p className="text-xs text-muted-foreground">
            {MODE_OPTIONS.find((o) => o.value === coachingMode)?.hint}
          </p>
        </div>

        <div className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-md border border-border p-3">
          {messages.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              {isInterviewMode
                ? "The stakeholder is ready. Ask your first clarifying question."
                : "Ask about this case."}
            </p>
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
            placeholder={isInterviewMode ? "Ask a clarifying question..." : "Ask anything about this case..."}
            rows={2}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleAsk();
              }
            }}
          />
          <Button onClick={handleAsk} disabled={activeMutation.isPending || !message.trim()} size="icon" aria-label="Ask">
            <Send className="size-4" aria-hidden="true" />
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
