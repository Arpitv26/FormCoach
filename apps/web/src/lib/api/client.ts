import type {
  AnalysisResponse,
  CoachRequest,
  CoachResponse,
  HealthResponse,
  LiveBatchRequest,
} from "./types";

export class ApiError extends Error {
  constructor(public status: number, message: string, public code?: string) {
    super(message);
    this.name = "ApiError";
  }
}

/** One boundary for backend URLs, errors, timeouts, and wire types. */
export function createApiClient(
  baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
  fetcher: typeof fetch = fetch,
) {
  async function request<T>(path: string, init?: RequestInit): Promise<T> {
    let response: Response;
    try {
      response = await fetcher(`${baseUrl.replace(/\/$/, "")}/api/v1${path}`, {
        ...init,
        signal: init?.signal ?? AbortSignal.timeout(15_000),
      });
    } catch {
      throw new ApiError(0, "Cannot reach the API. Check that the backend is running and try again.");
    }
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = body?.detail;
      const message = typeof detail?.message === "string"
        ? detail.message
        : response.status === 422
          ? "The request does not match the API contract. Check the submitted fields."
          : `API request failed (${response.status}).`;
      throw new ApiError(response.status, message, detail?.code);
    }
    if (!body || (path !== "/health" && body.contractVersion !== "1.0")) {
      throw new ApiError(response.status, "The API returned an unsupported or invalid response.");
    }
    // Pydantic validates server responses; contract tests check the shared fixtures.
    return body as T;
  }

  function post<T>(path: string, body: unknown) {
    return request<T>(path, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
  }

  return {
    health: () => request<HealthResponse>("/health"),
    analyzeLiveBatch: (batch: LiveBatchRequest) => post<AnalysisResponse>("/live/analyze-batch", batch),
    analyzeVideo: (file: File, exerciseHint?: string) => {
      const form = new FormData();
      form.append("file", file);
      if (exerciseHint) form.append("exerciseHint", exerciseHint);
      // The browser supplies the multipart boundary; do not set Content-Type yourself.
      return request<AnalysisResponse>("/videos/analyze", { method: "POST", body: form });
    },
    coach: (input: CoachRequest) => post<CoachResponse>("/coach", input),
  };
}

export const api = createApiClient();
