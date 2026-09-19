import { describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import * as navigation from "next/navigation";

import { SidebarNav } from "@/components/layout/sidebar-nav";

import { renderWithProviders } from "./test-utils";

vi.mock("next/navigation", () => ({
  usePathname: vi.fn(),
}));

vi.mock("@/features/auth/auth-provider", () => ({
  useAuth: () => ({ user: { ai_access_enabled: true } }),
}));

describe("SidebarNav", () => {
  it("highlights the active route and updates when the route changes", () => {
    vi.mocked(navigation.usePathname).mockReturnValue("/dashboard");
    const { rerender } = renderWithProviders(<SidebarNav />);

    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Curriculum" })).not.toHaveAttribute("aria-current");

    // Simulate navigating to /learn.
    vi.mocked(navigation.usePathname).mockReturnValue("/learn");
    rerender(<SidebarNav />);

    expect(screen.getByRole("link", { name: "Curriculum" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Dashboard" })).not.toHaveAttribute("aria-current");
  });

  it("does not expose administrator navigation in the learner sidebar", () => {
    vi.mocked(navigation.usePathname).mockReturnValue("/admin/content");
    renderWithProviders(<SidebarNav />);

    expect(screen.queryByRole("link", { name: "Content Admin" })).not.toBeInTheDocument();
  });
});
