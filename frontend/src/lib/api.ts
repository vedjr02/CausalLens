/** Base URL of the FastAPI statistical engine. */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Thin fetch wrapper that surfaces FastAPI's error detail instead of a bare status code. */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(
      "Could not reach the analysis engine. Is the backend running?",
    );
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // Non-JSON error body — keep the status-based message.
    }
    throw new ApiError(detail, response.status);
  }

  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
  environment: string;
}

export interface DbHealthResponse {
  configured: boolean;
  connected: boolean;
  server?: string;
  detail?: string;
}
