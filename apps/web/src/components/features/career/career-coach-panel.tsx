"use client";

import { useState } from "react";
import { Bot, Send } from "lucide-react";
import type { CareerCoachTopic } from "@data-analyst-lab/shared";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useCareerCoach } from "@/features/career/use-career";

const TOPIC_OPTIONS: { value: CareerCoachTopic; label: string }[] = [
  { value: "general", label: "General" },
  { value: "goal", label: "My Goals" },
  { value: "readiness", label: "Readiness" },
  { value: "weekly_review", label: "Weekly Review" },
  { value: "jd_prep", label: "Job Prep" },
];

interface ChatMessage {
  id: string;
  role: "USER" | "COACH";
  content: string;
}

/**
 * AI Career Coach — a minimal chat panel mirroring
 * components/features/ai/ai-mentor-panel.tsx's basic bubble UI. Unlike the
 * global AI Mentor, `POST /career/coach` has no matching conversation-history
 * endpoint, so this keeps its transcript in local component state rather than
 * fetching one.
 */
export function CareerCoachPanel({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const [topic, setTopic] = useState<CareerCoachTopic>("general");
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const askCoach = useCareerCoach();

  function handleAsk() {
    const trimmed = message.trim();
    if (!trimmed) return;
    setMessages((prev) => [...prev, { id: `user-${Date.now()}`, role: "USER", content: trimmed }]);
    askCoach.mutate(
      { message: trimmed, topic, conversation_id: conversationId ?? null },
      {
        onSuccess: (response) => {
          setConversationId(response.conversation_id);
          setMessages((prev) => [...prev, { id: response.message_id, role: "COACH", content: response.reply }]);
          setMessage("");
        },
      },
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="flex w-full max-w-md flex-col gap-4 sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Bot className="size-5" aria-hidden="true" />
            AI Career Coach
          </SheetTitle>
          <SheetDescription>
            Coaching on your goals, readiness, and job prep — every number it references is a platform estimate,
            never a hiring guarantee.
          </SheetDescription>
        </SheetHeader>

        <div className="flex items-center gap-2 px-4">
          <label className="shrink-0 text-xs font-medium text-muted-foreground" htmlFor="coach-topic">
            Topic
          </label>
          <Select
            id="coach-topic"
            value={topic}
            onChange={(event) => {
              setTopic(event.target.value as CareerCoachTopic);
              setConversationId(undefined);
            }}
            className="w-full sm:w-48"
          >
            {TOPIC_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="mx-4 flex flex-1 flex-col gap-3 overflow-y-auto rounded-md border border-sidebar-border p-3">
          {messages.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Ask about your goals, readiness, or how to prep for a specific role.
            </p>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={
                  m.role === "USER"
                    ? "max-w-[85%] self-end rounded-lg bg-primary/10 px-3 py-2 text-sm text-foreground"
                    : "max-w-[85%] self-start rounded-lg bg-muted px-3 py-2 text-sm whitespace-pre-wrap text-foreground"
                }
              >
                {m.content}
              </div>
            ))
          )}
        </div>

        <div className="flex gap-2 px-4 pb-4">
          <Textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Ask the career coach..."
            rows={2}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleAsk();
              }
            }}
          />
          <Button onClick={handleAsk} disabled={askCoach.isPending || !message.trim()} size="icon" aria-label="Ask">
            <Send className="size-4" aria-hidden="true" />
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
