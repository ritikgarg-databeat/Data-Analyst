import type { ReactElement, ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
import { render, type RenderOptions } from "@testing-library/react";

import { TooltipProvider } from "@/components/ui/tooltip";
import { ToastProvider } from "@/components/shared/toast-provider";

/** Fresh, retry-free QueryClient for each test — no network flakiness or delays. */
export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, gcTime: 0 },
    },
  });
}

// Mirrors app/providers.tsx's real provider stack — any hook a component under
// test relies on (e.g. useToast, used by an increasing number of mutations)
// should behave the same here as it does in the real app.
function AllProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={createTestQueryClient()}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <TooltipProvider>
          <ToastProvider>{children}</ToastProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export function renderWithProviders(ui: ReactElement, options?: Omit<RenderOptions, "wrapper">) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export * from "@testing-library/react";
