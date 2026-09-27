# FormCoach agent context

## Project and stopping point

FormCoach is a movement/fitness coaching demo for UBC BizTech HelloHacks 2026. Two beginner
developers have roughly a tomorrow-scale hackathon timeline. Prioritize a reliable
push-up demo using prerecorded gym video, clear evidence, and a polished presentation.
Judging: functionality 35%, pitch
25%, technical complexity 20%, UX/design 20%.

The bootstrap task ends with a verified shared foundation on main. Do not implement the
full product during bootstrap. Feature work begins after humans create their branches.
Future agents should implement the responsibilities in their handoff, not restart the design.

**Updated user priority:** prerecorded push-ups; no squat demo. B’s frontend PR #4 is now
merged and integrated on Computer A. Preserve the working upload and live analysis paths.
Keep the legacy squat fixture for compatibility, not as the intended presentation.

## Read before coding

1. README.md and docs/ARCHITECTURE.md.
2. docs/API_CONTRACT.md, contracts/README.md, and docs/DECISIONS.md.
3. Your docs/BACKEND_HANDOFF.md or docs/FRONTEND_HANDOFF.md.
4. docs/PRODUCT_SCOPE.md, docs/TASKS.md, and docs/SAFETY.md.
5. Backend measurement work: docs/EXERCISE_SYSTEM.md and docs/SCORING.md.
6. Coaching work: docs/AI_COACH.md.
7. Current remaining work and ownership transition: docs/NEXT_STEPS.md.

## Settled architecture

- Monorepo; independent Next.js/TypeScript frontend and FastAPI/Pydantic Python backend.
- Browser live pose extraction and backend uploaded-video extraction both produce our
  normalized `PoseFrame` representation. Analysis never depends on MediaPipe objects.
- Local video uses pretrained MediaPipe Pose Landmarker; no training a pose model from scratch.
- `MovementAnalyzer` is the shared interface for rules and possible later lightweight ML.
- Version `1.0` JSON contract; Python models -> checked-in schemas -> generated TS types.
- Stateless cumulative HTTP batches first. No database or WebSocket requirement.
- AI explains measured evidence. It cannot invent detections, diagnose, or predict injury.
- Coaching defaults to local. OpenAI requires explicit provider opt-in plus a backend key;
  the UI now requests short conversational replies with bounded history. Legacy evidence style
  still selects IDs/server wording. Read docs/AI_COACH.md; citations do not prove prose accuracy.
  Recognized missed-count disputes use local guidance; do not invent their cause. Mock JSON is synthetic.

## Ownership

| Branch / computer | Primary ownership |
| --- | --- |
| `backend-cv` / A | `apps/api/**`, including tests, CV, analysis, OpenAI integration |
| `frontend` / B | `apps/web/**`, including UI, webcam, API client, frontend tests |
| Deliberately coordinated | `contracts/**`, `docs/**`, `scripts/**`, `.github/**`, root config, README.md, AGENTS.md |

Avoid editing the other branch's directories. Shared changes should be rare, small, and
isolated. Generated `apps/web/src/lib/api/types.ts` is a coordinated exception: a shared
contract change must include matching types. Communicate with the other human before
relying on the change; do not send external messages on the human's behalf without authorization.

**Current human agreement (2026-09-26):** B handed off PR #4 with coach interactions, rep
comparisons and live counting. It is reviewed, merged into main (`767a98b`) and integrated
into backend-cv (`ae959a1`). A now owns the next frontend visual overhaul on this computer.
B should coordinate further screen edits. PR #5 is merged at `7f44566`. A physical rehearsal
failed: human 5 reps, detected 2. Read docs/LIVE_REHEARSAL_FIX.md before further counting work.

If a contract must change:

1. Explain the requirement and compatibility effect.
2. Update docs/API_CONTRACT.md and the Python domain models.
3. Update examples, regenerate schemas and TypeScript, and run contract checks.
4. Tell the other branch which commit to integrate before relying on it.
5. Merge that small shared change first; never quietly rename fields or exercise IDs.

## Working rules

- Never commit secrets, `.env` files, recordings, virtual environments, or build output.
- Give beginners exact commands, the folder to run them in, and expected output.
- Prefer reliable demo behavior over theoretical sophistication. Keep dependencies small.
- Do not add Docker, queues, Redis, authentication, cloud services, or databases without a concrete need.
- Keep functions small and testable. Do not rewrite unrelated code or the other team's work.
- Never fabricate scores or silently replace failed real requests with demo data.
- Preserve unknowns as `null`; show visibility/confidence limits. A selected exercise is not a detection.
- Do not infer biomechanical truth from a profile threshold. These are uncalibrated hackathon heuristics.
- Keep any provider credentials backend-only. `NEXT_PUBLIC_` variables are public.
- Run checks relevant to your changes (README and app READMEs list commands). Contract edits require both app checks.
- Use explicit files with `git add`; review the diff and commit frequently. Never force-push shared main.

## Current capabilities

**Independent movement feedback implemented:** read apps/api/MOVEMENT_OBSERVATIONS.md.
Additive `movementObservations` now describes sustained visible 2D body-line bends outside
completed reps. Five reviewed intervals on badpushups; original clip counts retained. Results
show time links and coach cards even with zero reps. These intervals can include setup, are
not attempt counts, and cannot label hip sag/pike or spinal posture. Both apps/schemas/types
must be updated together; older strict coach validators reject the additive field.

**Latest feedback checkpoint:** the human reports improved upload/live counting but zero
completed reps for deliberately changed torso/hip movement. See apps/api/BAD_MOVEMENT_REVIEW.md:
187/188 elbow samples usable, only one sample reaches the bend zone, so no sustained bend
qualifies. This is not bad-form recognition. Next priority in docs/NEXT_STEPS.md is descriptive
movement feedback outside completed reps. Do not force attempts into the completed-rep count.
Conversation evidence now prioritizes explicit requested rep numbers and recent user context;
an actual OpenAI request answered rep 12 correctly. Specific form assessment remains missing.

**Newest counting correction:** read apps/api/COUNTING.md. New live JSON reproduced 4 reps
and IMG_6943 upload 5. Counter v2 uses a 150° return zone and 60 ms raw dwell plus median
confirmation, collecting overlapping phase evidence together. Outputs: live JSON 5, IMG_6943
19; original five clips retain 3/1/1/2/4. Human reported 20; nineteen video cycle pairs were
reviewed, twentieth unestablished. Boundaries/measurements change; schemas do not. Squat
behavior is unchanged. Keep captures ignored and verify a fresh physical live set.

**Earlier display/UX correction:** live five-rep rehearsal failed (2 detected). A browser stale-display bug
could emit a false missing-pose sample before a valid frame. Fixed display/input separation;
no thresholds changed. New private capture download enables actual replay. Short conversational
coaching and simpler results replace the verbose panel. A fresh physical count is still required.
See docs/LIVE_REHEARSAL_FIX.md for the checks and remaining evidence.

**Previous integration:** PR #4 merged; 399 backend and 49 frontend tests, contracts, lint,
types and production build pass. Actual IMG_6942 browser upload/coaching/flag seeking pass;
simulated camera → actual API count/final/reset/stop pass. Physical webcam rehearsal and
independent timing validation remain open. Read docs/INTEGRATION_STATUS.md and NEXT_STEPS.md.

### Backend checkpoint before PR #4

**Latest checkpoint:** IMG_6942 counts 4 (normal/normal/slow/fast). It exposed a missed timing
flag under the old 20% reference gate. Timing policy v2 now requires a substantial change from
BOTH preceding durations, each using max(500 ms, 30% of that reference). Rep 3 now flags;
rep 4 remains unflagged. Read apps/api/COMPARISONS.md and REVIEW_6942.md. Unavailable comparisons
have rep-specific limitations; new numeric keys identify policy version/boundaries, with no
schema/type/endpoint changes. FRONTEND_HANDOFF and API_CONTRACT explain compatibility.
All five clips retain counts/measurements/timestamps; original four stay unflagged. 399 backend
and 35 frontend tests pass. Local coaching describes rep 3; no paid calls. This is development
regression evidence, not independent validation. Next: separate footage and B's integrated UI.
B's published branch remains `5dd6bb4`; frontend handoff/redesign is still pending.

### Earlier checkpoints (historical)

Health works. Pose analysis counts push-ups using elbow angles and retains the earlier squat
counter. It returns per-rep timestamps and smoothed angles; insufficient observations return null counts. Other hints or no
hint remain `not_implemented`. Scores stay null. Upload runs the optional local CV pipeline; coach defaults to a useful local fallback with an optional OpenAI evidence selector.
Frontend progress is tracked by remote commit in docs/INTEGRATION_STATUS.md. A local MediaPipe video adapter is available with optional dependencies; no form scorer is
integrated. Four real MOV recordings match human counts of 3, 1, 1, and 2 after a
phase-confirmation timing fix; see apps/api/VALIDATION.md for evidence and limitations.
HTTP upload integration now includes cleanup/error tests and a single-extraction gate.
Frontend PR #1 is merged into main and integrated into backend-cv without conflicts.
Upload/playback and the separate 240-second timeout passed a real-clip browser check;
read docs/INTEGRATION_STATUS.md. Next for B: coach panel and demo polish.
Push-up reps now include observed elbow excursion and timing around the minimum angle;
read apps/api/MEASUREMENTS.md. The new contracts/examples/pushup-analysis.json is synthetic.
Push-up comparisons now flag substantial duration changes or reduced observed excursion
against two preceding stable reps, with evidence and unknown confidence; see apps/api/COMPARISONS.md.
Real clips retain counts 3/1/1/2 and produce no flags; positive cases are synthetic so far.
B can integrate later. Evidence-only coaching, mocked SDK tests, and one live OpenAI QA
request are verified (2026-09-26, synthetic timing question, 3.22 seconds; docs/AI_COACH.md).
User authorized A to implement live camera and uploaded-video skeleton overlays on the
`pose-overlay` branch, based on backend PR #2. Read docs/POSE_OVERLAY.md before changing
camera/upload code. Live skeleton works locally; live counting is not connected. Existing
AnalysisResponse is unchanged; additive VideoAnalysisResponse includes the exact pose track.
The human reports physical-camera tracking works with some flicker. The `dde10e2` follow-up
fixes false Next.js startup errors and adds display-only smoothing. FRONTEND_HANDOFF.md is
refreshed for the complete checkpoint. Backend PR #2 and overlay PR #3 are merged into main
at `79f8da3`; B is integrating that baseline before completing the features listed above.
Next: physical webcam recheck after the fix, live counting integration, and real positive-case comparison validation. Recheck origin/frontend periodically and update
docs/INTEGRATION_STATUS.md. Keep form scoring deferred until evidence/calibration requirements are met.
Keep scores null until grounded scoring exists. Optional CV setup: apps/api/VIDEO_SETUP.md.
Read apps/api/README.md for counting limits and apps/api/examples/README.md for capture replay.

Tracking-feedback checkpoint: existing cameraQuality.issues now reports angle sample coverage,
named blocked joints and push-up shoulder/hip/ankle visibility coverage. No schema or counting
change; all scores/full-body visibility remain null. See apps/api/TRACKING_FEEDBACK.md:
311 tests passed at that checkpoint; saved-clip counts/rep details remained unchanged.
Real positive comparison footage is pending.
The body-line checkpoint now adds median shoulder–hip–ankle angles and sample counts to the
existing per-rep measurements dictionary. Read apps/api/BODY_LINE.md before interpreting them.
Same side as elbow; full observed rep coverage required; no form cue or score. Seven real-frame
overlays and independent arithmetic checked; existing counts/times/elbow measurements unchanged.
Body-line checkpoint checks: 335 backend tests, 35 frontend tests, lint/format/contracts/types and build pass.

Coach follow-up: descriptive body-line evidence is now available to local next-set feedback
and optional OpenAI selection. It requires consistent angle/side/sample metadata and retains
2D/median limitations. No alignment correction or score is inferred. Real positive comparison
footage and B's new frontend commits are still pending; preserve their active UI ownership.
Coach follow-up checks: 359 backend tests pass, plus lint, formatting and schema checks.
All four saved analyses pass local next-set HTTP coaching checks; no paid API calls were used.
Frontend code and contracts are unchanged by this follow-up.

Replay validation preparation: `app.tools.replay_live` now accepts exact expected timing/range
flag rep numbers (omitted = unchecked, empty option = expect none). It reports missing/extra
flags and exits 1 on mismatch; original frames/thresholds are unchanged. See apps/api/examples/README.md.
375 backend tests, lint/format/schema checks pass; four saved captures retain 3/1/1/2 reps and
pass explicit zero-flag checks. Real positive footage and B's handoff remain pending.

Latest human update: they still need to drive to the gym; the new recording and B's PR are
not ready. Continue checking published frontend commits periodically; do not assume a handoff.
Native backend rehearsal on `4b87e35` passed fresh uploads of all four original clips through
TestClient plus matching pose-track analysis and local coach evidence. Blank video returns
unknown count; corrupt-video error then recovery passes. See apps/api/VALIDATION.md for scope.
No runtime changes were needed. Remaining footage/browser checkpoints are still open.
