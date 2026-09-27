import type { AnalysisResponse, CoachRequest, CoachResponse } from "../api/types";

export interface CoachState {
  busy: boolean;
  mode: CoachRequest["mode"] | null;
  result: CoachResponse | null;
  error: string | null;
}
export const initialCoachState: CoachState = { busy: false, mode: null, result: null, error: null };

/** One analysis owns this controller. Replacing it aborts and discards older answers. */
export class CoachSession {
  private generation = 0;
  private controller: AbortController | null = null;
  private disposed = false;
  constructor(
    private analysis: AnalysisResponse,
    private request: (input: CoachRequest, signal: AbortSignal) => Promise<CoachResponse>,
    private onChange: (state: CoachState) => void,
  ) {}

  async submit(mode: CoachRequest["mode"], question = "") {
    if (this.disposed || this.controller) return;
    const trimmed = question.trim();
    if (mode === "qa" && (!trimmed || trimmed.length > 1000)) {
      this.onChange({ ...initialCoachState, error: "Enter a question between 1 and 1,000 characters." });
      return;
    }
    const generation = ++this.generation;
    const controller = new AbortController();
    this.controller = controller;
    this.onChange({ busy: true, mode, result: null, error: null });
    try {
      const result = await this.request({ analysis: this.analysis, mode, ...(mode === "qa" ? { question: trimmed } : {}) }, controller.signal);
      if (this.disposed || generation !== this.generation) return;
      if (result.sessionId !== this.analysis.sessionId || result.mode !== mode) throw new Error("The coach response did not match this request. Please try again.");
      this.onChange({ busy: false, mode, result, error: null });
    } catch (error) {
      if (this.disposed || generation !== this.generation) return;
      this.onChange({ busy: false, mode, result: null, error: error instanceof Error ? error.message : "The coach is unavailable. Please try again." });
    } finally {
      if (generation === this.generation) this.controller = null;
    }
  }

  cancel() {
    this.generation++;
    this.controller?.abort();
    this.controller = null;
    if (!this.disposed) this.onChange({ ...initialCoachState, error: "Stopped waiting. You can request another explanation." });
  }
  dispose() { this.disposed = true; this.cancel(); }
}
