"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

/**
 * Root error boundary (Next.js App Router convention — this file
 * automatically wraps every route). Previously there was NO error boundary
 * anywhere in the app: a real, traced bug class (an unguarded
 * `.toFixed()` on a value the API legitimately returns as null for a
 * routine degenerate input — zero-variance samples, a brand-new A/B test
 * with no conversions yet) threw an uncaught render error that blanked the
 * entire page with no recovery path. Those specific call sites are now
 * null-guarded, but this boundary is real defense-in-depth against the
 * next one, anywhere in the app, rather than a fix scoped to only the
 * cases already found.
 */
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const router = useRouter();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="size-6" aria-hidden="true" />
      </div>
      <div className="flex flex-col gap-1">
        <h1 className="text-lg font-semibold text-foreground">Something went wrong</h1>
        <p className="max-w-md text-sm text-muted-foreground">
          This page hit an unexpected error. You can try again, or head back to the dashboard.
        </p>
      </div>
      <div className="flex gap-2">
        <Button onClick={reset}>Try again</Button>
        <Button variant="outline" onClick={() => router.push("/")}>
          Go to Dashboard
        </Button>
      </div>
    </div>
  );
}
