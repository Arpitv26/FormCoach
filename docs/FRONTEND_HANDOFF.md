# Frontend handoff — Computer B

**Current checkpoint: 2026-09-26, including the camera logging/smoothing fix `dde10e2`.**
Read this file and AGENTS.md before continuing. This replaces the old bootstrap handoff.
The demo is **prerecorded push-ups**. Squat JSON is a legacy fixture, not the demo.

## Get all the work, in order

1. Frontend PR #1 is already merged into main.
2. Merge [backend PR #2](https://github.com/Arpitv26/helloHacks/pull/2) into main.
3. Merge the **`pose-overlay` → `main` PR** after its checks pass. It includes the upload
   skeleton, live skeleton, UI cleanup, startup-log fix, display smoothing, and this handoff.
4. Only after both feature PRs are merged, update Computer B using the commands below.

**PR #2 alone does not include the overlays.** `pose-overlay` contains all backend commits
plus the later overlay commits. Before #2 merges, the overlay PR also lists the backend
changes; after a normal merge of #2, its diff narrows to the overlay/handoff work.
Do not cherry-pick the individual fixes or overwrite the frontend directory with an old copy.

From your repository folder (the one containing `apps`), first run:

```bash
git status
```

If you have unfinished edits, save and commit your own work before merging. Do not discard
it. If Git already says `working tree clean`, continue. On Computer B's existing frontend branch:

```bash
git checkout frontend
git fetch origin
git merge origin/main
```

`fetch` downloads the published history. `merge` brings the integrated main into your frontend
branch while retaining your own commits. Success says `Already up to date`, `Fast-forward`, or
`Merge made`. If it reports `CONFLICT`, give the output to your coding agent to resolve; do not
choose all of one side. Then install the updated browser library/model and start the frontend:

```bash
cd apps/web
npm ci
npm run pose:setup
npm run dev
```

Successful setup prints `Browser pose assets ready`. Open http://localhost:3000.
If a frontend is already running, stop that terminal with **Control+C** before restarting.
The model downloads once; no OpenAI key or Python is needed for the live skeleton.
`npm run dev`/`build` recopy the runtime and apply the logging fix. After updating an already
open camera page, stop the camera, press **Command+Shift+R**, and enable it again.

## What already works — extend it, do not rebuild it

| Area | Current behavior |
| --- | --- |
| `/` | Exercise selection/landing interface; gym choices are planned analysis, not supported counters |
| `/upload` | File validation, local preview, real backend upload, cancellation/stale-response handling |
| Uploaded results | Rep count, per-rep elbow min/max/excursion, timing parts, review cues, timestamp jumps |
| Uploaded skeleton | Exact pose track from the same extraction, aligned with landscape/portrait playback; toggle on/off |
| `/camera?exercise=push-up` | Permission/error/stop states, local browser pose extraction and mirrored live skeleton |
| Display smoothing | Light live x/y smoothing only; raw analysis poses remain unchanged; lost/uncertain joints disappear |
| Startup logging | Known successful XNNPACK notice is informational; real errors are preserved |
| Backend coach | Local evidence summary plus optional OpenAI evidence selection; UI panel still needs integration |
| Unknowns | Scores remain null; no prominent empty score card; unmeasured elbow columns hidden; detailed limits expandable |

**Still unfinished:** live rep counting UI, coach panel, real positive comparison-case validation,
form scoring, automatic exercise recognition, other gym exercise analyzers, recording/history.
The human reports physical-camera tracking works with some flicker; the latest smoothing needs
another physical-camera comparison. Do not claim general tracking/form accuracy from this demo.

## Files you will use

All paths below are relative to `apps/web` unless specified.

| File | Responsibility |
| --- | --- |
| `src/app/page.tsx`, `src/lib/exercises.ts` | Exercise entry points and supported/planned labels |
| `src/components/video-upload.tsx` | Upload controls, player, overlay toggle, seeking |
| `src/lib/video/upload-session.ts` | File/result/pose pairing, aborts, object URL cleanup |
| `src/components/uploaded-results.tsx` | Actual upload result presentation |
| `src/components/playback-overlay.tsx` | Synchronize pose samples with the selected video |
| `src/components/webcam-setup.tsx`, `src/lib/camera/preview.ts` | Camera permissions and stream lifecycle |
| `src/components/live-overlay.tsx`, `src/lib/pose/live.ts` | Local model loading/inference and camera overlay lifecycle |
| `src/lib/pose/drawing.ts`, `display-filter.ts`, `names.ts` | Geometry for display, visual smoothing, canonical landmark mapping |
| `scripts/setup-pose.mjs`, `pose-runtime-logging.mjs` | Local model/runtime setup and exact startup-notice routing |
| `src/lib/api/client.ts` | Centralized URL, error handling, timeout and typed API methods |
| `src/lib/api/types.ts` | Generated contract types; never hand-edit |
| `src/lib/api/mock.ts` | Legacy squat fixture helper; not the push-up demo source |
| `tests/` | Camera, upload, client, contract, rendering and logging tests |

The older `SessionResults` component is not the current upload view. Its `partial` label says
“Set in progress”; fix that before reusing it, because final uploads can also be partial.

## API and rendering boundary

Read [API_CONTRACT.md](API_CONTRACT.md) and [POSE_OVERLAY.md](POSE_OVERLAY.md).
Contract version is still **1.0**; `AnalysisResponse` is unchanged.

- Upload UI calls `api.analyzeVideoWithPose(file, "push-up", signal)` and receives
  `{ contractVersion, analysis, poseTrack }`. Render `analysis`; keep `poseTrack` paired with
  the exact original file. The old `api.analyzeVideo` remains analysis-only for compatibility.
- Upload timeout is **240 seconds**; health/live/coach retain **15 seconds**. Do not retry
  automatically after timeout; backend processing may still be running.
- MP4/MOV/WebM, at most 250 MiB, 120 seconds and 4K. Setup/malformed/busy errors remain explicit.
- Coordinates refer to the upright **unmirrored** image. Mirror camera video/canvas together,
  never the data. Apply letterbox offsets. Anatomical left/right never swap in the contract.
- Playback uses milliseconds divided by 1000; hide missing/stale poses and do not interpolate
  across lost tracking. Native fullscreen/Picture-in-Picture omits the sibling canvas;
  use inline playback to demonstrate the overlay.
- Display filtering is visual only. Feed **raw mapped poses** to future movement analysis,
  never `DisplayPoseFilter` output. A visible skeleton is not a form score or readiness guarantee.
- Never overlay synthetic poses on a user's recording, invent scores, or replace failed real
  requests with mock data. `null` is unknown; zero is an actual measurement.
- Finalized `partial` means incomplete evidence, not necessarily an ongoing set. Empty issues
  do not establish good form. Full-body visibility/camera orientation are not verified.

Browser-only tracking works on Computer B without a backend. Real upload/coach requests need
an API. The default `http://localhost:8000` means **Computer B's own computer**, not Computer A.
For same-machine backend setup, follow [BEGINNER_SETUP.md](BEGINNER_SETUP.md) and
[VIDEO_SETUP.md](../apps/api/VIDEO_SETUP.md). Coordinate networking separately if using A's API;
do not put A's key in a frontend env variable. Preserve existing `.env.local` settings.

## Mock data for independent UI work

Use these repository-root files directly when the backend is unavailable, with visible
synthetic labels. None has a matching recording.

- `contracts/examples/pushup-analysis.json`: one synthetic measured-geometry rep, null scores.
- `contracts/examples/pushup-comparison-analysis.json`: three synthetic reps with review flags.
- `contracts/examples/pushup-video-with-pose.json`: synthetic analysis + pose envelope shape.
- `contracts/examples/live-pose-batch.json`: tiny request-shape example, not enough to count reps.
- `contracts/examples/squat-analysis.json`: legacy scored UI fixture only; do not rename its
  knee measurements as push-up findings.

## Next frontend work, in small tested commits

1. **Coach panel:** call `api.coach({ analysis, mode: "summary" })` using the current result.
   Modes are `summary`, `next_set`, `qa` (QA requires a nonblank question). Display `message`,
   `provider`, `evidence` paths and `limitations`; discard responses for replaced uploads.
   No browser key. Read [AI_COACH.md](AI_COACH.md).
2. **Presentation polish:** make rep comparisons readable, show existing issue explanations as
   “Changes to review”, improve focus/mobile layout, and rehearse timestamp jumps. Use supplied
   numeric evidence; timing parts are not isolated lifting/lowering durations. No “worst rep”
   ranking when every score is null. Read [MEASUREMENTS.md](../apps/api/MEASUREMENTS.md) and
   [COMPARISONS.md](../apps/api/COMPARISONS.md).
3. **Coordinate live counting with A:** the backend already accepts cumulative pose snapshots.
   Add explicit start/finish/reset, a new session/time zero, fixed dimensions and hint, at most
   1800 frames / 120 seconds, one request in flight, stale-response rejection and a final
   `isFinal: true` snapshot. Replace displayed counts; never add successive totals. The current
   live renderer samples at up to 10 fps; the contract ceiling is 15 fps. Keep rep math in Python.
4. **Demo check:** actual laptop webcam after the logging fix, slow/missing model, no person,
   stop/restart/navigation, backend down, upload cancellation, and one landscape/portrait clip.

A owns measurement algorithms and real positive-case validation. B owns frontend code again
following the user-authorized overlay work by A. Avoid overlapping edits to camera/upload files;
coordinate the next live-counting change before starting it on both computers.

## Checks and known evidence

Most recent checkpoint: **300 backend tests, 35 frontend tests**, lint, types, contract checks
and production build pass. Landscape/portrait upload skeleton alignment and simulated-camera
stop/restart/missing-model behavior were checked in Chrome. The follow-up dev-browser check
asserts zero XNNPACK console errors, not just absence of uncaught exceptions.

From `apps/web`, before committing:

```bash
npm run contracts:check
npm run lint
npm run typecheck
npm test
npm run build
```

Success ends in matching types, passing tests and a successful Next.js build. Backend/CV
validation details: [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md),
[POSE_OVERLAY.md](POSE_OVERLAY.md), [VALIDATION.md](../apps/api/VALIDATION.md).
Keys, personal recordings, downloaded model/runtime binaries and generated build output
are intentionally not in Git. `npm ci` plus `npm run pose:setup` restores browser dependencies.
