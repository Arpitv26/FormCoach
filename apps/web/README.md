# FormCoach web — Computer B

Read [AGENTS.md](../../AGENTS.md), [frontend handoff](../../docs/FRONTEND_HANDOFF.md),
[API contract](../../docs/API_CONTRACT.md), and [beginner setup](../../docs/BEGINNER_SETUP.md).
Use Node 24. Frontend feature work stays in `apps/web`; the backend owns rep math.

## Run the frontend

From the repository root:

```bash
cd apps/web
npm ci
```

If `.env.local` does not exist, copy `.env.example` to it once. Preserve existing settings.
Then run:

```bash
npm run pose:setup
npm run dev
```

Expect `Browser pose assets ready`, then a localhost URL. Open http://localhost:3000.
The model download is needed once for browser skeletons; `dev` and `build` copy the pinned
runtime locally. Stop the server with **Control+C**. Later starts only need `npm run dev`.
See [pose setup and limitations](../../docs/POSE_OVERLAY.md).

The browser can preview a camera and track a skeleton without a backend. **Upload analysis,
live rep counting, and coaching require the backend.** Set `NEXT_PUBLIC_API_BASE_URL` in
`.env.local` (normally `http://localhost:8000`). `localhost` refers to this computer; use a
reachable address and coordinate CORS if the backend runs on your teammate's computer.
Restart dev or rebuild after changing the URL. Never put keys in `NEXT_PUBLIC_` settings.

The updated backend and overlays are integrated into this branch. For a same-machine API,
follow `apps/api/README.md`; upload processing additionally needs `apps/api/VIDEO_SETUP.md`.
There is no root npm workspace: run npm commands in `apps/web`.

## Push-up uploads and review

Open `/upload`, or choose **Analyze a push-up video** on the homepage. Record a clear side-view
set of 3–5 push-ups, transfer it to your computer, and choose the original clip. Preview stays
local until **Analyze push-ups** uploads it. MP4/MOV/WebM are accepted, up to 250 MiB,
120 seconds, 4K total pixels, and 4096 pixels on either axis. The backend validates decoding.

The UI calls `/api/v1/videos/analyze-with-pose` with multipart `file` and `exerciseHint=push-up`.
Its response pairs measured analysis and the exact pose track with the selected file.
Skeletons follow inline video playback and can be toggled off. Native fullscreen and
Picture-in-Picture show video without the sibling overlay.

Results include counts, per-rep timing and elbow movement, switchable measurement charts,
reference comparisons, and **Changes to review** with supplied explanations and uncertainty.
Chart bars are descriptive values, not scores or rankings. Review buttons seek only within
the matching measured upload. Missing values stay unknown; absent comparisons are not zero.
A final `partial` result can indicate incomplete evidence, not ongoing recording.

Uploads use a 240-second timeout. Other calls retain 15 seconds. Stop waiting, removal,
replacement, and route navigation abort client requests and release obsolete local video URLs.
Native backend extraction may continue; wait before retrying. No automatic retry or mock
fallback is used. Codec errors suggest exporting H.264 MP4 and analyzing that exact export.

## Coach

After an upload or finalized live set, **Explain my set**, **Next set**, and **Ask coach** send
only the current `AnalysisResponse`, mode, and optional question to `/api/v1/coach`.
The frontend never sends video or pose tracks to the coach. Requests start only on user action.

The panel displays the message, actual provider, supporting evidence (including dot paths),
and limitations. Evidence links can jump to a rep in a matching upload. The local fallback
supports summaries and next-set guidance without a key. Free-form questions require the
optional backend OpenAI provider; local QA returns an honest unsupported response.
Questions must be nonblank and at most 1,000 characters. The backend may send the question
and numeric statements to OpenAI when configured; keys remain backend-only.

Cancel, new clips, new analyses, and leaving the route discard obsolete answers. Network
errors stay visible, with explicit retry controls; there is no browser-generated advice.
See [coach behavior](../../docs/AI_COACH.md) and `apps/api/COACH_SETUP.md` for backend setup.

## Webcam and live counting

Open `/camera?exercise=push-up`, select **Enable camera**, and allow access. Once the local
pose model loads, **Start set** begins sampling raw, unmirrored coordinates and sending them
to the backend. The preview and skeleton are mirrored together for display. Display smoothing
never modifies analysis poses. No microphone, camera video upload, or recording is used.

- Each set has a new session ID and time zero, fixed image dimensions, and the `push-up` hint.
- Up to 10 samples/second; cumulative snapshots about once/second; one request in flight.
- Counts replace the previous backend result. A dash is unknown; zero is a known count.
- Missing poses remain empty frames. No interpolation across tracking gaps.
- **Finish set** freezes capture and sends `isFinal: true` after any pending update completes.
- **Stop camera**, lost camera/model, hidden page, changed dimensions, and the two-minute limit
  end capture. Navigating away or resetting aborts and discards obsolete requests.
- **Reset set** clears poses/results; **New set** resets after completion. Neither retains history.
- API errors pause capture with the last successful result labeled as such. **Retry final analysis**
  sends the frozen cumulative snapshot; there are no automatic retries.
- Backend rules decide which cycles count. The UI does not infer readiness from a skeleton,
  force-complete unfinished reps, or compute scores.

A real physical-camera set still needs comparison against a human count on the demo machine.
Browser tests use a simulated camera and controlled API responses, not a counting-accuracy benchmark.

Gym choices (incline dumbbell bench, cable lateral raise, lat pulldown, triceps pushdown)
remain skeleton/framing previews with `backendHint: null`. Changing exercises stops the camera
and clears any live set. Do not send those routing slugs to analysis until A implements agreed IDs.

## Verification and files

From `apps/web`:

```bash
npm run contracts:check
npm run lint
npm run typecheck
npm test
npm run build
```

After a build, `npm start` serves a production preview. Use [DEMO_CHECKS.md](DEMO_CHECKS.md)
for the physical-camera and real-backend rehearsal before merging.

- `src/lib/api/client.ts`: typed HTTP boundary, abort signals, version checks and timeouts.
- `src/lib/coach/`: one-analysis request lifecycle and safe evidence lookup.
- `src/lib/live/session.ts`: cumulative capture, finalization and stale-response protection.
- `src/lib/results/measurements.ts`: presentation of supplied values/reference differences.
- `src/components/uploaded-results.tsx`: upload and finalized live results, charts and coach.
- `src/components/live-overlay.tsx`: raw poses to analysis; smoothed poses to drawing only.
- `src/lib/api/types.ts`: generated. Coordinate changes; never edit manually.

Tests exercise camera/upload cleanup, coach modes and stale responses, cumulative live
requests/limits/finalization/errors, evidence paths, measurement rendering and shared contracts.
The canonical fixtures are synthetic and have no matching video. No fixtures are substituted
for failed real requests. Legacy squat data is used only in tests and the older result component.

Do not commit keys, `.env` files, recordings, pose captures, model/runtime binaries, or build output.
ESLint is temporarily pinned to 9.39.5 for Next.js plugin compatibility; see DECISIONS.md.
The browser boundary checks HTTP errors and contract version; backend Pydantic validates the
full shape. Any future untrusted external response source needs a coordinated validation decision.
