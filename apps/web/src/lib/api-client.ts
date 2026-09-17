import type { ApiErrorResponse } from "@data-analyst-lab/shared";

/**
 * Base URL for the FastAPI backend. Configurable via NEXT_PUBLIC_API_URL,
 * falling back to the local default used throughout development.
 */
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

/**
 * Typed error thrown by the API client for any non-2xx response, or when the
 * network request itself fails (e.g. the API is not running yet).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown> | null;

  constructor(
    status: number,
    code: string,
    message: string,
    details?: Record<string, unknown> | null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** True when the request never reached the server (e.g. API is offline). */
  get isNetworkError(): boolean {
    return this.status === 0;
  }
}

export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

async function request<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { body, headers, ...rest } = options;

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
      ...rest,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...headers,
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (cause) {
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      "Unable to reach the Personal Data Analyst Lab API. Is it running?",
      { cause: cause instanceof Error ? cause.message : String(cause) },
    );
  }

  if (!response.ok) {
    let payload: ApiErrorResponse | null = null;
    try {
      payload = (await response.json()) as ApiErrorResponse;
    } catch {
      // No JSON body on the error response — fall through to the default message.
    }
    throw new ApiError(
      response.status,
      payload?.error?.code ?? "UNKNOWN_ERROR",
      payload?.error?.message ?? response.statusText ?? "Request failed",
      payload?.error?.details ?? null,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/**
 * POSTs a `multipart/form-data` request — used for dataset file uploads
 * (Phase 5). Takes native `File` objects straight from an `<input>` or
 * drag-and-drop event and streams them via `FormData`/`fetch`, the same way
 * a plain HTML form would — the browser never buffers the whole file into a
 * JS string/array first, so this stays memory-safe for large files.
 */
async function postForm<T>(
  path: string,
  files: File[],
  fields: Record<string, string> = {},
): Promise<T> {
  const form = new FormData();
  for (const file of files) form.append("files", file);
  for (const [key, value] of Object.entries(fields)) form.append(key, value);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
      method: "POST",
      body: form,
      // No Content-Type header — the browser sets the multipart boundary itself.
      headers: { Accept: "application/json" },
    });
  } catch (cause) {
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      "Unable to reach the Personal Data Analyst Lab API. Is it running?",
      { cause: cause instanceof Error ? cause.message : String(cause) },
    );
  }

  if (!response.ok) {
    let payload: ApiErrorResponse | null = null;
    try {
      payload = (await response.json()) as ApiErrorResponse;
    } catch {
      // No JSON body on the error response — fall through to the default message.
    }
    throw new ApiError(
      response.status,
      payload?.error?.code ?? "UNKNOWN_ERROR",
      payload?.error?.message ?? response.statusText ?? "Request failed",
      payload?.error?.details ?? null,
    );
  }

  return (await response.json()) as T;
}

/**
 * POSTs a single `multipart/form-data` file under the field name `file`,
 * plus optional extra string fields — used by the resume/JD real file-upload
 * endpoints (Phase 12 follow-up), which extract real text server-side
 * (.txt/.docx/.pdf) instead of the browser reading `file.text()` (which
 * silently produces garbage — even a save-breaking literal NUL byte — for
 * any non-plain-text file).
 */
async function postFile<T>(
  path: string,
  file: File,
  fields: Record<string, string> = {},
): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  for (const [key, value] of Object.entries(fields)) form.append(key, value);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
      method: "POST",
      body: form,
      headers: { Accept: "application/json" },
    });
  } catch (cause) {
    throw new ApiError(
      0,
      "NETWORK_ERROR",
      "Unable to reach the Personal Data Analyst Lab API. Is it running?",
      { cause: cause instanceof Error ? cause.message : String(cause) },
    );
  }

  if (!response.ok) {
    let payload: ApiErrorResponse | null = null;
    try {
      payload = (await response.json()) as ApiErrorResponse;
    } catch {
      // No JSON body on the error response — fall through to the default message.
    }
    throw new ApiError(
      response.status,
      payload?.error?.code ?? "UNKNOWN_ERROR",
      payload?.error?.message ?? response.statusText ?? "Request failed",
      payload?.error?.details ?? null,
    );
  }

  return (await response.json()) as T;
}

export const apiClient = {
  get: <T>(path: string, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  postForm,
  postFile,
  patch: <T>(path: string, body?: unknown, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  put: <T>(path: string, body?: unknown, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "PUT", body }),
  delete: <T>(path: string, options?: ApiRequestOptions) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
