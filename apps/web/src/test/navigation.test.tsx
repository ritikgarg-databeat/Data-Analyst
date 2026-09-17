import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import * as navigation from "next/navigation";

import { SidebarNav } from "@/components/layout/sidebar-nav";

import { renderWithProviders } from "./test-utils";

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(),
}));

describe("SidebarNav", () => {
  it("highlights the active route and updates when the route changes", () => {
    vi.mocked(navigation.usePathname).mockReturnValue("/");
    const { rerender } = renderWithProviders(<SidebarNav />);

    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Curriculum" })).not.toHaveAttribute("aria-current");

    // Simulate navigating to /learn.
    vi.mocked(navigation.usePathname).mockReturnValue("/learn");
    rerender(<SidebarNav />);

    expect(screen.getByRole("link", { name: "Curriculum" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Dashboard" })).not.toHaveAttribute("aria-current");
  });

  it("treats nested routes (e.g. /admin/content) as active for their nav item", () => {
    vi.mocked(navigation.usePathname).mockReturnValue("/admin/content");
    renderWithProviders(<SidebarNav />);

    expect(screen.getByRole("link", { name: "Content Admin" })).toHaveAttribute("aria-current", "page");
  });
});
