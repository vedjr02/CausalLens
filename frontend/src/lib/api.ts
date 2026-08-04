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
    throw new ApiError(await readErrorDetail(response), response.status);
  }

  return response.json() as Promise<T>;
}

/**
 * FastAPI reports errors two ways: a plain string `detail` from an explicit
 * HTTPException, or an array of field errors from request validation. Both
 * need to reach the user as a readable sentence.
 */
async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = body?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          const message = String(item?.msg ?? "").replace(/^Value error,\s*/, "");
          const field = Array.isArray(item?.loc)
            ? item.loc.filter((p: unknown) => p !== "body").join(".")
            : "";
          return field && !message.toLowerCase().includes(field.toLowerCase())
            ? `${field}: ${message}`
            : message;
        })
        .filter(Boolean);
      if (messages.length) return messages.join(" ");
    }
  } catch {
    // Non-JSON error body — fall through to the status-based message.
  }
  return `Request failed (${response.status})`;
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
