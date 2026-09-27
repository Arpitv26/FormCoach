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

**Updated user priority:** prerecorded push-ups; no squat demo. Computer B is still building
the frontend. Do not wait on browser tracking to implement backend video pose extraction.
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
  it selects evidence IDs and the server renders wording. Read docs/AI_COACH.md. Mock JSON is synthetic.

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

**Current human agreement (2026-09-26):** B is finishing coach interactions, rep comparisons,
results polish, live counting and demo verification. A continues backend work now. After B
hands off a committed, reviewed and integrated PR, A owns the frontend visual overhaul on
this computer. Do not start that overhaul while B is editing these screens.

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
