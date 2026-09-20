import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useMediaQuery } from "@/lib/use-media-query";

function MediaQueryProbe() {
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  return <p>{isDesktop ? "Desktop panels" : "Stacked workspace"}</p>;
}

describe("responsive layout primitives", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("keeps long tab lists horizontally reachable on narrow screens", () => {
    render(
      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="ai">AI</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
        </TabsList>
      </Tabs>,
    );

    expect(screen.getByRole("tablist")).toHaveClass("w-full", "max-w-full", "overflow-x-auto");
    expect(screen.getAllByRole("tab")[0]).toHaveClass("flex-none", "whitespace-nowrap");
  });

  it("switches structural layouts when the desktop breakpoint changes", () => {
    let matches = false;
    const listeners = new Set<() => void>();
    const media = {
      get matches() {
        return matches;
      },
      media: "(min-width: 1024px)",
      onchange: null,
      addEventListener: (_type: string, listener: () => void) => listeners.add(listener),
      removeEventListener: (_type: string, listener: () => void) => listeners.delete(listener),
      addListener: (listener: () => void) => listeners.add(listener),
      removeListener: (listener: () => void) => listeners.delete(listener),
      dispatchEvent: () => true,
    } as unknown as MediaQueryList;
    vi.stubGlobal("matchMedia", vi.fn(() => media));

    render(<MediaQueryProbe />);
    expect(screen.getByText("Stacked workspace")).toBeInTheDocument();

    act(() => {
      matches = true;
      listeners.forEach((listener) => listener());
    });

    expect(screen.getByText("Desktop panels")).toBeInTheDocument();
  });
});
