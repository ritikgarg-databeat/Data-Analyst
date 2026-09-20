import { NextRequest } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteContext = { params: Promise<{ path: string[] }> };
const CONTROL_PATHS = new Set(["auth", "health", "users"]);
// Render's free instances can need about a minute to wake. Authentication and
// health requests are the control plane for the UI, so keep them open long
// enough to bridge a normal cold start instead of surfacing a false outage.
const DEFAULT_CONTROL_TIMEOUT_MS = 90_000;

const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "content-length",
  "expect",
  "host",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
]);

function proxyTarget(): string {
  return (process.env.API_PROXY_TARGET?.trim() || "http://127.0.0.1:8000").replace(/\/+$/, "");
}

function requestHeaders(request: NextRequest): Headers {
  const headers = new Headers(request.headers);
  for (const name of HOP_BY_HOP_HEADERS) headers.delete(name);
  headers.delete("accept-encoding");
  headers.set("x-forwarded-host", request.headers.get("host") ?? request.nextUrl.host);
  headers.set("x-forwarded-proto", request.nextUrl.protocol.replace(":", ""));
  return headers;
}

function responseHeaders(upstream: Response): Headers {
  const headers = new Headers();
  upstream.headers.forEach((value, name) => {
    if (!HOP_BY_HOP_HEADERS.has(name) && name !== "content-encoding" && name !== "set-cookie") {
      headers.append(name, value);
    }
  });

  const cookieHeaders = upstream.headers as Headers & { getSetCookie?: () => string[] };
  const cookies = cookieHeaders.getSetCookie?.() ?? [];
  if (cookies.length) {
    for (const cookie of cookies) headers.append("set-cookie", cookie);
  } else {
    const combinedCookie = upstream.headers.get("set-cookie");
    if (combinedCookie) headers.append("set-cookie", combinedCookie);
  }
  return headers;
}

async function forward(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const target = new URL(`${proxyTarget()}/api/v1/${path.map(encodeURIComponent).join("/")}`);
  target.search = request.nextUrl.search;

  const init: RequestInit & { duplex?: "half" } = {
    method: request.method,
    headers: requestHeaders(request),
    redirect: "manual",
    cache: "no-store",
  };
  if (CONTROL_PATHS.has(path[0])) {
    const configuredTimeout = Number(process.env.API_PROXY_CONTROL_TIMEOUT_MS);
    const timeout = Number.isFinite(configuredTimeout) && configuredTimeout >= 1_000
      ? configuredTimeout
      : DEFAULT_CONTROL_TIMEOUT_MS;
    init.signal = AbortSignal.timeout(timeout);
  }
  if (request.method !== "GET" && request.method !== "HEAD" && request.body) {
    init.body = request.body;
    init.duplex = "half";
  }

  try {
    const upstream = await fetch(target, init);
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders(upstream),
    });
  } catch (error) {
    const cause = error instanceof Error && "cause" in error ? error.cause : undefined;
    console.error(
      "Data Lab API gateway request failed:",
      error instanceof Error ? error.message : "Unknown upstream error",
      cause instanceof Error ? cause.message : "",
    );
    const errorName = typeof error === "object" && error && "name" in error ? String(error.name) : "";
    const causeName = typeof cause === "object" && cause && "name" in cause ? String(cause.name) : "";
    const timedOut = [errorName, causeName].some(name => name === "TimeoutError" || name === "AbortError");
    return Response.json(
      {
        error: {
          code: timedOut ? "API_STARTING" : "API_UNAVAILABLE",
          message: timedOut
            ? "Your Data Lab workspace is starting. Please retry shortly."
            : "Unable to reach the Data Lab API.",
        },
      },
      {
        status: timedOut ? 503 : 502,
        headers: { "Cache-Control": "no-store", ...(timedOut ? { "Retry-After": "5" } : {}) },
      },
    );
  }
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
export const OPTIONS = forward;
