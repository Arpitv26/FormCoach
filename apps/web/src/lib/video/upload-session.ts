import { ApiError } from "../api/client";
import type { AnalysisResponse } from "../api/types";

export const MAX_VIDEO_BYTES = 250 * 1024 * 1024;
const serverMayContinue = "The server may still be processing. Wait before trying again.";

export function validateVideo(file: Pick<File, "name" | "size">): string | null {
  if (!/\.(mp4|mov|webm)$/i.test(file.name)) return "Choose an MP4, MOV, or WebM video.";
  if (file.size === 0) return "This file is empty. Choose another video.";
  if (file.size > MAX_VIDEO_BYTES) return "Choose a video smaller than 250 MiB.";
  return null;
}

export function validateMetadata(duration: number, width: number, height: number): string | null {
  if (Number.isFinite(duration) && duration > 120) return "Trim your video to two minutes or less, then choose the new clip.";
  if (width * height > 3840 * 2160 || Math.max(width, height) > 4096) return "Export your clip at 4K or lower (maximum dimension 4096 pixels).";
  return null;
}

export function uploadError(error: unknown): string {
  if (!(error instanceof ApiError)) return "Analysis could not finish. Please try again.";
  switch (error.code) {
    case "VIDEO_ANALYSIS_NOT_IMPLEMENTED": return "Video analysis is unavailable on this backend. Connect the updated backend-cv server to analyze push-ups.";
    case "VIDEO_SETUP_REQUIRED": return "The backend needs its video dependencies and pose model installed. Ask your backend teammate to finish video setup.";
    case "VIDEO_PROCESSOR_BUSY": return "The server is processing another video. Wait for it to finish, then try again.";
    case "REQUEST_TIMEOUT":
    case "VIDEO_PROCESSING_TIMEOUT": return `Analysis took too long. ${serverMayContinue} Try a shorter clip on your next attempt.`;
    case "REQUEST_ABORTED": return `Stopped waiting. ${serverMayContinue}`;
    case "INVALID_VIDEO":
    case "UNSUPPORTED_VIDEO_TYPE": return `${error.message} Try exporting an H.264 MP4, then choose and analyze that export.`;
    default: return error.message;
  }
}

export interface UploadState {
  selection: { file: File; url: string } | null;
  phase: "ready" | "analyzing" | "complete" | "error";
  preview: "loading" | "ready" | "unplayable";
  validationError: string | null;
  message: string | null;
  result: AnalysisResponse | null;
}
export const emptyUploadState: UploadState = {
  selection: null, phase: "ready", preview: "loading", validationError: null, message: null, result: null,
};

/** Owns each file/response pair and releases obsolete requests and object URLs. */
export class UploadSession {
  private state: UploadState = { ...emptyUploadState };
  private generation = 0;
  private controller: AbortController | null = null;
  private disposed = false;

  constructor(
    private readonly analyze: (file: File, signal: AbortSignal) => Promise<AnalysisResponse>,
    private readonly onChange: (state: UploadState) => void,
    private readonly urls: Pick<typeof URL, "createObjectURL" | "revokeObjectURL"> = URL,
  ) {}

  private update(patch: Partial<UploadState>) {
    if (this.disposed) return;
    this.state = { ...this.state, ...patch };
    this.onChange(this.state);
  }

  private release() {
    this.generation++;
    this.controller?.abort();
    this.controller = null;
    if (this.state.selection) this.urls.revokeObjectURL(this.state.selection.url);
  }

  select(file: File | null) {
    if (this.disposed) return;
    const wasAnalyzing = this.state.phase === "analyzing";
    this.release();
    const validationError = file ? validateVideo(file) : null;
    this.update({ ...emptyUploadState, validationError,
      message: wasAnalyzing ? serverMayContinue : null,
      selection: file && !validationError ? { file, url: this.urls.createObjectURL(file) } : null,
    });
  }

  metadata(url: string, duration: number, width: number, height: number) {
    if (this.state.selection?.url !== url) return;
    this.update({ preview: "ready", validationError: validateMetadata(duration, width, height) });
  }

  previewFailed(url: string) {
    if (this.state.selection?.url === url) this.update({ preview: "unplayable" });
  }

  async submit() {
    const { selection, validationError } = this.state;
    if (this.disposed || !selection || validationError || this.controller) return;
    const generation = ++this.generation;
    const controller = new AbortController();
    this.controller = controller;
    this.update({ phase: "analyzing", message: null, result: null });
    try {
      const result = await this.analyze(selection.file, controller.signal);
      if (generation !== this.generation || this.disposed) return;
      this.update({ phase: "complete", result });
    } catch (error) {
      if (generation !== this.generation || this.disposed) return;
      this.update({ phase: "error", message: uploadError(error) });
    } finally {
      if (generation === this.generation) this.controller = null;
    }
  }

  cancel() {
    if (!this.controller) return;
    this.generation++;
    this.controller.abort();
    this.controller = null;
    this.update({ phase: "ready", message: `Stopped waiting. ${serverMayContinue}` });
  }

  dispose() {
    this.disposed = true;
    this.release();
  }
}
