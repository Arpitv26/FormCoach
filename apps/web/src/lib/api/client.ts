import type {
  AnalysisResponse,
  CoachRequest,
  CoachResponse,
  HealthResponse,
  LiveBatchRequest,
  VideoAnalysisResponse,
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
  async function request<T>(path: string, init?: RequestInit, timeoutMs = 15_000): Promise<T> {
    let response: Response;
    let body;
    const deadline = AbortSignal.timeout(timeoutMs);
    const signal = init?.signal ? AbortSignal.any([init.signal, deadline]) : deadline;
    try {
      signal.throwIfAborted();
      response = await fetcher(`${baseUrl.replace(/\/$/, "")}/api/v1${path}`, {
        ...init,
        signal,
      });
      body = await response.json().catch((error) => {
        signal.throwIfAborted();
        if (error instanceof SyntaxError) return null;
        throw error;
      });
      signal.throwIfAborted();
    } catch {
      if (signal.aborted) {
        const timedOut = signal.reason?.name === "TimeoutError";
        throw new ApiError(0, timedOut ? "The request timed out." : "The request was cancelled.", timedOut ? "REQUEST_TIMEOUT" : "REQUEST_ABORTED");
      }
      throw new ApiError(0, "Cannot reach the API. Check that the backend is running and try again.");
    }
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

  function post<T>(path: string, body: unknown, signal?: AbortSignal) {
    return request<T>(path, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal,
    });
  }

  return {
    health: () => request<HealthResponse>("/health"),
    analyzeLiveBatch: (batch: LiveBatchRequest, signal?: AbortSignal) => post<AnalysisResponse>("/live/analyze-batch", batch, signal),
    analyzeVideo: (file: File, exerciseHint?: string, signal?: AbortSignal) => {
      const form = new FormData();
      form.append("file", file);
      if (exerciseHint) form.append("exerciseHint", exerciseHint);
      // The browser supplies the multipart boundary; do not set Content-Type yourself.
      return request<AnalysisResponse>("/videos/analyze", { method: "POST", body: form, signal }, 240_000);
    },
    coach: (input: CoachRequest, signal?: AbortSignal) => post<CoachResponse>("/coach", input, signal),
    analyzeVideoWithPose: (file: File, exerciseHint: string, signal?: AbortSignal) => {
      const form = new FormData();
      form.append("file", file);
      form.append("exerciseHint", exerciseHint);
      return request<VideoAnalysisResponse>("/videos/analyze-with-pose", { method: "POST", body: form, signal }, 240_000);
    },
  };
}

export const api = createApiClient();
