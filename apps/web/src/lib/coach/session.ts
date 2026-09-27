import type { AnalysisResponse, CoachRequest, CoachResponse } from "../api/types";

export interface CoachExchange { question: string; response: CoachResponse }
export interface CoachState {
  busy: boolean;
  mode: CoachRequest["mode"] | null;
  result: CoachResponse | null;
  error: string | null;
  exchanges: CoachExchange[];
}
export const initialCoachState: CoachState = { busy: false, mode: null, result: null, error: null, exchanges: [] };

/** One analysis owns a bounded conversation. Replacing the set discards its history. */
export class CoachSession {
  private generation = 0;
  private controller: AbortController | null = null;
  private disposed = false;
  private exchanges: CoachExchange[] = [];
  constructor(
    private analysis: AnalysisResponse,
    private request: (input: CoachRequest, signal: AbortSignal) => Promise<CoachResponse>,
    private onChange: (state: CoachState) => void,
  ) {}

  private update(patch: Partial<CoachState>) {
    this.onChange({ ...initialCoachState, exchanges: [...this.exchanges], ...patch });
  }

  async submit(mode: CoachRequest["mode"], question = "") {
    if (this.disposed || this.controller) return;
    const trimmed = question.trim();
    if (mode === "qa" && (!trimmed || trimmed.length > 1000)) {
      this.update({ error: "Enter a question between 1 and 1,000 characters." }); return;
    }
    const prompt = mode === "summary" ? "How did my set go?" : mode === "next_set" ? "What should I focus on next?" : trimmed;
    const generation = ++this.generation;
    const controller = new AbortController();
    this.controller = controller;
    this.update({ busy: true, mode });
    try {
      const history = this.exchanges.slice(-6).flatMap((turn) => [
        { role: "user" as const, content: turn.question },
        { role: "assistant" as const, content: turn.response.message.slice(0, 2000) },
      ]);
      const result = await this.request({ analysis: this.analysis, mode, responseStyle: "conversation", history,
        ...(mode === "qa" ? { question: trimmed } : {}) }, controller.signal);
      if (this.disposed || generation !== this.generation) return;
      if (result.sessionId !== this.analysis.sessionId || result.mode !== mode) throw new Error("The coach response did not match this request. Please try again.");
      this.exchanges = [...this.exchanges, { question: prompt, response: result }].slice(-6);
      this.update({ mode, result });
    } catch (error) {
      if (this.disposed || generation !== this.generation) return;
      this.update({ mode, error: error instanceof Error ? error.message : "The coach is unavailable. Please try again." });
    } finally {
      if (generation === this.generation) this.controller = null;
    }
  }

  cancel() {
    this.generation++;
    this.controller?.abort(); this.controller = null;
    if (!this.disposed) this.update({ error: "Stopped waiting. You can request another explanation." });
  }
  dispose() { this.disposed = true; this.cancel(); }
}
