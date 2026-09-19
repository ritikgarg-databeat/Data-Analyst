import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/v1/[...path]/route";

describe("same-origin API gateway", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns a retryable response while the API is cold-starting", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new DOMException("Timed out", "TimeoutError"));

    const response = await GET(
      new NextRequest("http://localhost/api/v1/health"),
      { params: Promise.resolve({ path: ["health"] }) },
    );

    expect(response.status).toBe(503);
    expect(response.headers.get("retry-after")).toBe("5");
    await expect(response.json()).resolves.toMatchObject({
      error: { code: "API_STARTING" },
    });
  });
});
