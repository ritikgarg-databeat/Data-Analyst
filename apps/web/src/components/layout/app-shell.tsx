import type { ReactNode } from "react";

import { AIMentorLauncher } from "./ai-mentor-launcher";
import { CommandPaletteProvider } from "./command-palette";
import { DesktopSidebar } from "./desktop-sidebar";
import { TopBar } from "./top-bar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <CommandPaletteProvider>
      <div className="flex min-h-svh w-full min-w-0 overflow-x-clip bg-background">
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        <DesktopSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main id="main-content" className="min-w-0 flex-1 px-3 py-5 min-[380px]:px-4 sm:px-6 sm:py-6 lg:px-8">
            {children}
          </main>
        </div>
        <AIMentorLauncher />
      </div>
    </CommandPaletteProvider>
  );
}
