"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { Sparkles } from "lucide-react";

import { AIMentorPanel } from "@/components/features/ai/ai-mentor-panel";
import { Button } from "@/components/ui/button";

/**
 * Globally-accessible AI Mentor launcher (spec section 6) — rendered once in
 * AppShell so it's a floating action button on every route, independent of
 * per-page code.
 */
export function AIMentorLauncher() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  // /ai/mentor already embeds the full chat inline — the floating launcher
  // would open a second, entirely independent AIMentorChat instance stacked
  // on top of it (separate message/conversation state, confusing duplicate
  // surfaces).
  if (pathname === "/ai/mentor") return null;

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        className="fixed right-5 bottom-5 z-40 gap-2 rounded-full shadow-lg"
        size="lg"
      >
        <Sparkles className="size-4" aria-hidden="true" />
        AI Mentor
      </Button>
      <AIMentorPanel open={open} onOpenChange={setOpen} />
    </>
  );
}
