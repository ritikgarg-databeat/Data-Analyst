import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { proxy } from "@/proxy";

describe("authentication proxy", () => {
  it("keeps the public landing page reachable without a cookie", () => {
    const response = proxy(new NextRequest("http://localhost/"));
    expect(response.headers.get("location")).toBeNull();
  });

  it("never redirects the same-origin API gateway", () => {
    const response = proxy(new NextRequest("http://localhost/api/v1/auth/login", { method: "POST" }));
    expect(response.headers.get("location")).toBeNull();
  });

  it("redirects a protected learner route when no access cookie exists", () => {
    const response = proxy(new NextRequest("http://localhost/profile"));
    expect(response.headers.get("location")).toBe("http://localhost/login");
  });

  it("redirects an admin route to the separate admin login", () => {
    const response = proxy(new NextRequest("http://localhost/admin/users"));
    expect(response.headers.get("location")).toBe("http://localhost/admin/login");
  });

  it("allows protected routes optimistically when the cookie is present", () => {
    const request = new NextRequest("http://localhost/profile", {
      headers: { cookie: "dal_access_token=opaque" },
    });
    expect(proxy(request).headers.get("location")).toBeNull();
  });

  it("keeps login reachable with a stale cookie", () => {
    const request = new NextRequest("http://localhost/login", {
      headers: { cookie: "dal_access_token=expired" },
    });
    expect(proxy(request).headers.get("location")).toBeNull();
  });
});
