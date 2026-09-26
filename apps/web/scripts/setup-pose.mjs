import { cp, mkdir, rename, access } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("..", import.meta.url));
const output = join(root, "public", "pose");
await mkdir(output, { recursive: true });
await cp(join(root, "node_modules", "@mediapipe", "tasks-vision", "wasm"), join(output, "wasm"), { recursive: true });
if (process.argv.includes("--model")) {
  const target = join(output, "pose_landmarker_lite.task");
  try {
    await access(target);
    console.log("Pose model already installed.");
  } catch {
    const response = await fetch("https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task", { signal: AbortSignal.timeout(120_000) });
    if (!response.ok) throw new Error(`Pose download failed (${response.status}). Run npm run pose:setup again.`);
    const { writeFile } = await import("node:fs/promises");
    const bytes = new Uint8Array(await response.arrayBuffer());
    if (bytes.length < 1_000_000) throw new Error("Pose model download was incomplete.");
    await writeFile(`${target}.download`, bytes);
    await rename(`${target}.download`, target);
    console.log("Pose model installed locally.");
  }
}
console.log("Browser pose assets ready in public/pose (ignored by Git).");
