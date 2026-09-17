import type { ReactNode } from "react";

import { AIMentorLauncher } from "./ai-mentor-launcher";
import { CommandPaletteProvider } from "./command-palette";
import { DesktopSidebar } from "./desktop-sidebar";
import { TopBar } from "./top-bar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <CommandPaletteProvider>
      <div className="flex min-h-svh w-full bg-background">
        <a href="#main-content" className="skip-link">
          Skip to content
        </a>
        <DesktopSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main id="main-content" className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
            {children}
          </main>
        </div>
        <AIMentorLauncher />
      </div>
    </CommandPaletteProvider>
  );
}
