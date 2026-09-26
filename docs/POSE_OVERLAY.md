# Skeleton overlay checkpoint

The user authorized Computer A to implement the camera/upload UI for this feature while
Computer B was not editing those screens. Work is on `pose-overlay`, based on `backend-cv`
at `f049013`. It does not change the existing backend PR #2. Merge #2 first, then review
this feature against main. B should integrate the feature commit before editing these screens.

## Try it on Computer A

The model is already downloaded on this computer. Leave your backend and frontend terminals
running. Open http://localhost:3000/camera?exercise=push-up and click **Enable camera**.
Allow the browser's camera prompt. After “Loading skeleton tracking”, visible joints should
appear over your mirrored preview. Click **Stop camera** to release the camera and model.
This is live skeleton tracking; live rep counting is not connected in this checkpoint.

For prerecorded analysis, open http://localhost:3000/upload, choose a push-up clip, and click
**Analyze push-ups**. When the results arrive, press play or choose a rep timestamp. Toggle
**Show skeleton** to compare with the original image. Reanalyze an already-open clip after
updating the app; previous responses did not contain pose frames.

## First setup on Computer B / another clone

From the repository folder containing `apps`:

```bash
cd apps/web
npm ci
npm run pose:setup
npm run dev
```

`pose:setup` downloads Google's pretrained Pose Landmarker Lite model once and copies the
installed package's WebAssembly runtime into `public/pose`. Successful output includes
`Pose model installed locally` and `Browser pose assets ready`. This requires internet for
the download, no API key. Subsequent browser inference uses local files and works offline.
`npm run dev` prints a localhost URL. If port 3000 is occupied, stop the old frontend with
Control+C before restarting; the backend permits port 3000 by default.

If the model download fails, rerun `npm run pose:setup`. If tracking fails, stop/restart the
camera; if needed run that setup command and reload. Camera access requires localhost or
HTTPS. Missing model/permission errors stay visible; a working preview does not imply tracking.
The setup command preserves an existing model. If a local model is corrupt, rename
`apps/web/public/pose/pose_landmarker_lite.task` in Finder and rerun setup.

Uploaded analysis also requires Computer A's Python CV setup; see
[VIDEO_SETUP.md](../apps/api/VIDEO_SETUP.md). Browser tracking alone needs no backend.
No frames are sent to the backend or OpenAI from the camera screen. No microphone or recording.

## Implementation

- `@mediapipe/tasks-vision` **1.0.1**, local Pose Landmarker Lite float16 revision 1 for live.
  Existing uploaded-video adapter uses the Full model; estimates can differ between models.
- `src/lib/pose/live.ts` maps provider output into our unmirrored canonical `PoseFrame`.
  Detect up to two people; output empty landmarks unless exactly one pose is available.
  Preview inference is capped at 10 fps on the browser main thread, CPU, one call at a time.
  This is a small first implementation; slower devices can still hitch during synchronous
  inference. Measure on the demo laptop before moving inference to a worker.
- `src/lib/pose/drawing.ts` draws torso/limb/foot joints, visibility >=0.7, no offscreen
  clamping or gap interpolation. Face and finger detail are deliberately omitted.
- `LiveOverlay` mirrors the canvas and video together, clears stalled/hidden frames, and
  closes the detector on stop/unmount, including late model initialization.
- `PlaybackOverlay` uses the additive `/videos/analyze-with-pose` endpoint and the original
  browser file. One extraction returns both analysis and a bounded pose track. No server cache.
  File replacement/cancellation cannot attach an old track to a new video.
- `UploadSession` still accepts old analysis-only callers; the current upload screen requests
  the new envelope. Old endpoint clients continue working unchanged.
- Playback uses a maximum 150 ms old sample, clears while seeking, and supports contained
  landscape/portrait images. Native video fullscreen/Picture-in-Picture excludes the overlay;
  use inline playback for the demo. The overlay is visual only; text measurements remain accessible.
- Model/runtime files, real recordings and extracted poses are ignored by Git. CI checks code
  and contracts without downloading a model. Run `pose:setup` before a live demo or deployment.

## Verified on Computer A — 2026-09-26

- **300 backend tests, 35 frontend tests**, lint, type checks and contract checks pass.
- Python tests cover matching analysis, single extraction, temporal/dimension bounds,
  portrait metadata, empty frames, cleanup, existing endpoint compatibility and synthetic schema.
- Frontend tests cover aspect-ratio offsets, seeking/gaps, visibility, canonical mapping,
  stopped initialization cleanup, and file/pose pairing, alongside existing camera/upload tests.
- Chrome upload of `IMG_6939.MOV` and rotated portrait `IMG_6938.MOV`: one rep each;
  46 and 53 pose samples respectively. Minimum-angle seek and skeleton alignment visually
  inspected. Toggle/clear work; 390px mobile layouts have no horizontal overflow.
- Chrome simulated camera fed the actual `IMG_6939` recording: real browser model detected
  joints and rendered mirrored overlay. Stop/restart released tracks; missing model showed
  an error and camera stop still worked. No live backend requests or uncaught page errors.
- Production build and production-browser simulated-camera smoke check pass. **Physical webcam, Safari, and mobile inference speed still need
  a human demo check.** Simulated-camera success is not a general tracking accuracy benchmark.

## Next checkpoint

Keep the prerecorded demo stable. Check the actual laptop webcam with the human present.
Then connect cumulative live pose snapshots to the existing analyzer: fixed dimensions,
new session/time zero, one request at a time, bounded 120s/1800 frames, stale-response rejection,
and finalization. Do not copy rep math into React. Scoring, biomechanical form judgments,
deadlift analysis and automatic exercise recognition remain separate unfinished features.

Provider reference: [Google's browser Pose Landmarker guide](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/web_js).

## Physical-camera follow-up: startup logging and jitter

The human reported a working physical camera with some flicker and a red Next.js console
error for `INFO: Created TensorFlow Lite XNNPACK delegate for CPU.` This is a successful
native initialization notice emitted on stderr. The original browser check caught it in
console output but only asserted against uncaught exceptions; that missed the Next.js issue UI.

`setup-pose.mjs` now adapts the copied runtime's local error logger to send **only that exact
single-argument notice** to `console.info`. All other diagnostics remain errors. It does not
patch the application's global console or node_modules. The adapter fails clearly if an SDK
upgrade changes its expected logging declaration. Predev/prebuild and pose:setup apply it.
Refresh the camera page after updating to load the corrected runtime; restarting the frontend
also regenerates these ignored assets automatically.

`DisplayPoseFilter` lightly smooths live x/y display positions with a 70 ms exponential
filter. It never changes raw input poses, recorded playback, or analyzer measurements.
It immediately drops joints below the existing visibility threshold, resets on empty/missing
poses, gaps over 150 ms, nonincreasing timestamps, or large jumps. This reduces small position
jitter; uncertain joints can still disappear. It does not establish form or tracking accuracy.

Verification: 35 frontend tests, lint and typecheck pass. The development browser's real model
with a simulated camera now emits **zero XNNPACK console errors**, renders joints, restarts and
releases the camera, and still exposes the deliberate missing-model failure. A new test checks
that other error messages remain errors. Physical-camera smoothness still needs the human's
comparison after refresh. PR #2 is separate, mergeable, and its exact head CI passed.
