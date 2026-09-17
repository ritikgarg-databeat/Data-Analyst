import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { AIChatResponse, AIConversation, AISettings } from "@data-analyst-lab/shared";

import { AIMentorPanel } from "@/components/features/ai/ai-mentor-panel";
import { apiClient } from "@/lib/api-client";

import { renderWithProviders } from "./test-utils";

vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    postForm: vi.fn(),
    patch: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
  API_BASE_URL: "http://localhost:8000",
  ApiError: class ApiError extends Error {},
}));

function makeSettings(overrides: Partial<AISettings> = {}): AISettings {
  return {
    id: "settings-1",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    enabled: true,
    provider_override: null,
    model_override: null,
    response_style: "balanced",
    learning_mode: "socratic",
    privacy_preference: "standard",
    max_context_chars: null,
    daily_request_limit: null,
    effective_provider: "local",
    ai_configured: true,
    ...overrides,
  };
}

function makeChatResponse(overrides: Partial<AIChatResponse> = {}): AIChatResponse {
  return {
    conversation_id: "conv-1",
    message_id: "msg-1",
    reply: "Here's a hint about primary keys.",
    structured: null,
    hint_level: null,
    provider: "local",
    model: "local",
    ai_configured: true,
    ...overrides,
  };
}

function makeConversation(overrides: Partial<AIConversation> = {}): AIConversation {
  return {
    id: "conv-1",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    feature: "MENTOR",
    title: null,
    context_type: "general",
    context_id: null,
    is_archived: false,
    last_message_at: "2026-01-01T00:00:00Z",
    messages: [
      { id: "m1", role: "USER", content: "What is a primary key?", structured_output: null, hint_level: null, created_at: "2026-01-01T00:00:00Z" },
      { id: "m2", role: "ASSISTANT", content: "Here's a hint about primary keys.", structured_output: null, hint_level: null, created_at: "2026-01-01T00:00:00Z" },
    ],
    ...overrides,
  };
}

describe("AIMentorPanel", () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
  });

  it("shows the privacy notice and lets the learner send a message", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/ai/settings") return makeSettings();
      if (path.startsWith("/ai/conversations/")) return makeConversation();
      throw new Error(`Unhandled GET ${path}`);
    });
    vi.mocked(apiClient.post).mockResolvedValue(makeChatResponse());

    renderWithProviders(<AIMentorPanel open onOpenChange={() => {}} />);

    expect(await screen.findByText(/may send selected learning\/code\/data context/)).toBeInTheDocument();

    const textbox = screen.getByPlaceholderText("Ask anything...");
    fireEvent.change(textbox, { target: { value: "What is a primary key?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() =>
      expect(apiClient.post).toHaveBeenCalledWith(
        "/ai/mentor",
        expect.objectContaining({ message: "What is a primary key?", context_type: "general" }),
      ),
    );

    expect(await screen.findByText("Here's a hint about primary keys.")).toBeInTheDocument();
  });

  it("shows a local-placeholder notice under the platform's zero-config default", async () => {
    /**
     * Regression test — this banner used to gate on `ai_configured`, which
     * `Settings.ai_configured` (app/core/config.py) always returns `true` for
     * local mode by design ("local never needs a key, so it counts as
     * configured"). Since `AI_PROVIDER=local` is the platform's own default,
     * `!ai_configured` was never true under default config, so this
     * disclosure — specifically about the local placeholder — could never
     * actually appear. It now gates on `effective_provider === "local"`
     * directly, matching what the text itself describes.
     */
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/ai/settings") return makeSettings({ effective_provider: "local" });
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<AIMentorPanel open onOpenChange={() => {}} />);

    expect(await screen.findByText(/No AI provider is configured yet/)).toBeInTheDocument();
  });

  it("does not show the local-placeholder notice once a real provider is configured", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/ai/settings") {
        return makeSettings({ effective_provider: "openai", ai_configured: true });
      }
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<AIMentorPanel open onOpenChange={() => {}} />);

    await screen.findByText(/may send selected learning\/code\/data context/);
    expect(screen.queryByText(/No AI provider is configured yet/)).not.toBeInTheDocument();
  });

  it("switching context to Current Case reveals an attempt-id input", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path === "/ai/settings") return makeSettings();
      throw new Error(`Unhandled GET ${path}`);
    });

    renderWithProviders(<AIMentorPanel open onOpenChange={() => {}} />);
    await screen.findByText(/may send selected learning\/code\/data context/);

    fireEvent.change(screen.getByLabelText("Context"), { target: { value: "case" } });
    expect(screen.getByPlaceholderText("Case attempt ID")).toBeInTheDocument();
  });
});
