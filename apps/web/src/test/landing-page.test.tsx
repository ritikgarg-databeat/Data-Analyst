import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import LandingPage from "@/app/page";

import { renderWithProviders } from "./test-utils";

const postMock = vi.hoisted(() => vi.fn());

vi.mock("@/lib/api-client", () => ({
  apiClient: { post: postMock },
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));

vi.mock("@/features/auth/auth-provider", () => ({
  useAuth: () => ({ setAuthenticatedUser: vi.fn() }),
}));

describe("LandingPage", () => {
  beforeEach(() => {
    postMock.mockReset();
    window.history.replaceState(null, "", "/");
  });

  it("presents the Data Lab product and opens authentication in place", async () => {
    const user = userEvent.setup();
    renderWithProviders(<LandingPage />);

    expect(screen.getByRole("heading", { name: /Learn real data skills.*Build proof.*Walk in ready/i })).toBeInTheDocument();
    expect(screen.getByText(/personal data lab combines a modern curriculum/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /A complete path from first query to career-ready/i })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /create/i }).length).toBeGreaterThan(0);

    await user.click(screen.getAllByRole("button", { name: "Sign in" })[0]);
    expect(screen.getByRole("heading", { name: "Sign in to Data Lab" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enter your workspace" })).toBeInTheDocument();
  });

  it("opens direct signup links in the landing modal", async () => {
    window.history.replaceState(null, "", "/?auth=signup");
    renderWithProviders(<LandingPage />);

    expect(await screen.findByRole("heading", { name: "Create your Data Lab account" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Begin your journey" })).toBeInTheDocument();
  });

  it("plays the path-unlocked transition after successful authentication", async () => {
    const user = userEvent.setup();
    postMock.mockResolvedValue({
      user: {
        id: "user-1",
        name: "Jordan Lee",
        email: "jordan@example.com",
        role: "USER",
        status: "ACTIVE",
        must_change_password: false,
        ai_access_enabled: false,
        ai_daily_quota: 0,
        ai_requests_today: 0,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      },
    });
    renderWithProviders(<LandingPage />);

    await user.click(screen.getAllByRole("button", { name: "Sign in" })[0]);
    await user.type(screen.getByPlaceholderText("you@example.com"), "jordan@example.com");
    await user.type(screen.getByPlaceholderText("Enter your password"), "a secure password");
    await user.click(screen.getByRole("button", { name: "Enter your workspace" }));

    expect(await screen.findByText("Path unlocked")).toBeInTheDocument();
    expect(screen.getByText("Your next chapter is opening.")).toBeInTheDocument();
  });
});
