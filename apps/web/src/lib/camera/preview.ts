export type CameraState = {
  phase: "idle" | "requesting" | "starting" | "live" | "stopped" | "error";
  message: string;
};

export const initialCameraState: CameraState = {
  phase: "idle",
  message: "Enable your camera when you’re ready. Your browser may ask for permission.",
};

export function cameraErrorMessage(error: unknown): string {
  const name = error instanceof Error ? error.name : "";
  switch (name) {
    case "NotAllowedError":
    case "SecurityError":
      return "Camera access was blocked. Allow camera access in your browser’s site settings and your device’s privacy settings, then try again.";
    case "NotFoundError":
      return "No camera was found. Connect or enable a camera, then try again.";
    case "NotReadableError":
    case "AbortError":
      return "The camera could not start. Close other apps using it, check your device settings, then try again.";
    case "OverconstrainedError":
      return "This camera could not provide a preview. Try another camera or browser.";
    default:
      return "The camera could not be opened. Check that it is connected and allowed in your browser, then try again.";
  }
}

/** Owns one preview stream; late permission/playback results cannot revive a stopped camera. */
export class CameraPreview {
  private generation = 0;
  private disposed = false;
  private pending = false;
  private stream: MediaStream | null = null;
  private removeListeners: (() => void) | null = null;

  constructor(
    private video: Pick<HTMLVideoElement, "srcObject" | "play" | "pause">,
    private getMedia: () => Promise<MediaStream>,
    private onChange: (state: CameraState) => void,
  ) {}

  private release() {
    this.removeListeners?.();
    this.removeListeners = null;
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
    this.video.pause();
    this.video.srcObject = null;
  }

  private current(generation: number) {
    return !this.disposed && generation === this.generation;
  }

  private fail(generation: number, message: string) {
    if (!this.current(generation)) return;
    this.generation++;
    this.pending = false;
    this.release();
    this.onChange({ phase: "error", message });
  }

  async start() {
    if (this.disposed || this.pending || this.stream) return;
    const generation = ++this.generation;
    this.pending = true;
    this.onChange({ phase: "requesting", message: "Allow camera access in your browser’s prompt. You can cancel below if you’re not ready." });

    let stream: MediaStream;
    try {
      stream = await this.getMedia();
    } catch (error) {
      this.fail(generation, cameraErrorMessage(error));
      return;
    }

    if (!this.current(generation)) {
      stream.getTracks().forEach((track) => track.stop());
      return;
    }
    this.stream = stream;
    const tracks = stream.getVideoTracks();
    if (!tracks.length || tracks.some((track) => track.readyState === "ended")) {
      this.fail(generation, "The camera disconnected before the preview started. Reconnect it and try again.");
      return;
    }
    const onEnded = () => this.fail(generation, "The camera disconnected or access was revoked. Check your camera and permissions, then try again.");
    tracks.forEach((track) => track.addEventListener("ended", onEnded));
    this.removeListeners = () => tracks.forEach((track) => track.removeEventListener("ended", onEnded));
    this.video.srcObject = stream;
    this.onChange({ phase: "starting", message: "Camera access granted. Opening the preview…" });

    try {
      await this.video.play();
      if (!this.current(generation)) return;
      this.pending = false;
      this.onChange({ phase: "live", message: "Your camera preview is on. Use the framing tips to position yourself; body visibility has not been evaluated." });
    } catch {
      this.fail(generation, "The preview could not play. Try again, or open this page in another browser.");
    }
  }

  stop() {
    if (this.disposed) return;
    this.generation++;
    this.pending = false;
    this.release();
    this.onChange({ phase: "stopped", message: "Camera stopped. If a browser permission prompt is still open, dismiss it. You can enable the camera again when ready." });
  }

  dispose() {
    this.disposed = true;
    this.generation++;
    this.release();
  }
}
