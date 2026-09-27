import type { AnalysisResponse, LiveBatchRequest, PoseFrame } from "../api/types";

export const LIVE_LIMIT_MS = 120_000;
export const LIVE_FRAME_LIMIT = 1800;
export interface LiveState {
  phase: "idle" | "capturing" | "finishing" | "finished" | "error";
  sessionId: string | null;
  elapsedMs: number;
  frameCount: number;
  inFlight: boolean;
  result: AnalysisResponse | null;
  message: string | null;
  error: string | null;
}
export const initialLiveState: LiveState = {
  phase: "idle", sessionId: null, elapsedMs: 0, frameCount: 0, inFlight: false, result: null, message: null, error: null,
};

/** Cumulative raw poses only. The backend owns readiness, comparisons and rep counting. */
export class LiveSession {
  private state: LiveState = { ...initialLiveState };
  private frames: PoseFrame[] = [];
  private dimensions = { imageWidth: 0, imageHeight: 0 };
  private startedAt = 0;
  private lastSentAt = 0;
  private generation = 0;
  private controller: AbortController | null = null;
  private disposed = false;

  constructor(
    private analyze: (batch: LiveBatchRequest, signal: AbortSignal) => Promise<AnalysisResponse>,
    private onChange: (state: LiveState) => void,
    private now: () => number = () => performance.now(),
    private newId: () => string = () => crypto.randomUUID(),
  ) {}

  private update(patch: Partial<LiveState>) {
    if (this.disposed) return;
    this.state = { ...this.state, ...patch };
    this.onChange(this.state);
  }

  start(width: number, height: number) {
    if (this.disposed || this.state.phase === "capturing" || this.state.phase === "finishing") return;
    if (![width, height].every((n) => Number.isInteger(n) && n > 0 && n <= 16384)) {
      this.update({ error: "Wait for the camera image before starting." }); return;
    }
    this.reset();
    this.dimensions = { imageWidth: width, imageHeight: height };
    this.startedAt = this.now();
    this.lastSentAt = this.startedAt;
    this.update({ phase: "capturing", sessionId: this.newId(), message: "Start in a straight-arm top position. Only completed cycles are counted." });
  }

  capture(frame: PoseFrame | null, width: number, height: number, capturedAt = this.now()) {
    if (this.disposed || this.state.phase !== "capturing") return;
    if (width !== this.dimensions.imageWidth || height !== this.dimensions.imageHeight) {
      this.finish("The camera dimensions changed. This set has ended; start a new set for the new view."); return;
    }
    const timestampMs = Math.round(capturedAt - this.startedAt);
    if (timestampMs < 0) return;
    if (timestampMs > LIVE_LIMIT_MS) { this.finish("The two-minute set limit was reached."); return; }
    const previous = this.frames.at(-1);
    // Limit to 10 fps, preserve missing-pose frames, and never renumber time across gaps.
    if (previous && timestampMs - previous.timestampMs < 100) return;
    if (this.frames.length >= LIVE_FRAME_LIMIT) { this.finish("The frame limit was reached."); return; }
    this.frames.push({ frameIndex: this.frames.length, timestampMs,
      landmarks: frame ? frame.landmarks.map((point) => ({ ...point })) : [],
    });
    if (this.frames.length === LIVE_FRAME_LIMIT || timestampMs === LIVE_LIMIT_MS) this.finish("The set limit was reached.");
  }

  pulse() {
    if (this.disposed || this.state.phase !== "capturing") return;
    const elapsedMs = Math.min(LIVE_LIMIT_MS, Math.max(0, Math.round(this.now() - this.startedAt)));
    this.update({ elapsedMs, frameCount: this.frames.length });
    if (elapsedMs >= LIVE_LIMIT_MS) { this.finish("The two-minute set limit was reached."); return; }
    if (!this.controller && this.frames.length && this.now() - this.lastSentAt >= 1000) void this.send(false);
  }

  finish(message?: string) {
    if (this.disposed || this.state.phase !== "capturing") return;
    this.update({ phase: "finishing", frameCount: this.frames.length,
      elapsedMs: Math.min(LIVE_LIMIT_MS, Math.max(0, Math.round(this.now() - this.startedAt))),
      message: message ?? "Set ended. Waiting for the final analysis…",
    });
    if (!this.controller) void this.send(true);
  }

  retryFinal() {
    if (this.disposed || this.state.phase !== "error" || this.controller || !this.state.sessionId) return;
    this.update({ phase: "finishing", error: null, message: "Retrying the final snapshot of this set…" });
    void this.send(true);
  }

  private async send(isFinal: boolean) {
    if (this.disposed || this.controller || !this.state.sessionId) return;
    const generation = this.generation;
    const controller = new AbortController();
    this.controller = controller;
    this.lastSentAt = this.now();
    const batch: LiveBatchRequest = { contractVersion: "1.0", sessionId: this.state.sessionId,
      exerciseHint: "push-up", ...this.dimensions, frames: this.frames.slice(), isFinal,
    };
    this.update({ inFlight: true });
    try {
      const result = await this.analyze(batch, controller.signal);
      if (this.disposed || generation !== this.generation) return;
      if (result.sessionId !== batch.sessionId || result.source.type !== "live") throw new Error("The response did not match this live set.");
      const waitingMessage = this.state.message === "Set ended. Waiting for the final analysis…" || this.state.message === "Retrying the final snapshot of this set…";
      this.update({ result, ...(isFinal ? { phase: "finished" as const, message: waitingMessage ? "Final analysis received." : this.state.message } : {}) });
    } catch (error) {
      if (this.disposed || generation !== this.generation) return;
      this.update({ phase: "error", frameCount: this.frames.length, message: "Capture paused. Retry the final analysis or reset to start a new set.", error: error instanceof Error ? error.message : "Live analysis could not finish." });
    } finally {
      if (!this.disposed && generation === this.generation) {
        this.controller = null;
        this.update({ inFlight: false });
        // Finish queued during a regular request uses the latest full snapshot, exactly once.
        if (!isFinal && this.state.phase === "finishing") void this.send(true);
      }
    }
  }

  /** Explicit local export for replay; contains landmarks, never video or credentials. */
  snapshot(): LiveBatchRequest | null {
    if (!this.state.sessionId || this.state.phase === "capturing" || this.state.phase === "finishing") return null;
    return { contractVersion: "1.0", sessionId: this.state.sessionId, exerciseHint: "push-up",
      ...this.dimensions, isFinal: true, frames: this.frames.map((frame) => ({ ...frame, landmarks: frame.landmarks.map((point) => ({ ...point })) })) };
  }

  reset() {
    this.generation++;
    this.controller?.abort();
    this.controller = null;
    this.frames = [];
    this.update({ ...initialLiveState });
  }
  dispose() { this.disposed = true; this.reset(); }
}
