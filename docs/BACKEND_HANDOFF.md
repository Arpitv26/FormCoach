# Backend / CV / ML / AI handoff — Computer A

Read AGENTS.md, ARCHITECTURE.md, API_CONTRACT.md, EXERCISE_SYSTEM.md, SCORING.md, and SAFETY.md.
Your branch is `backend-cv`; your primary ownership is **apps/api/**. Follow BEGINNER_SETUP.md.
Computer B builds the UI independently from the shared fixture. Preserve its contract.

**User priority change:** prerecorded push-ups, no squat demo. The push-up elbow counter
and local MediaPipe video adapter now match human counts on four real recordings (3, 1, 1, 2).
Read apps/api/VALIDATION.md for the timing fix and limits. Next integrate the upload route;
do not wait for browser tracking. The original squat mock
remains a legacy fixture. See apps/api/examples/README.md for the replay workflow.

## What is already wired

- FastAPI health/live/upload/coach routes and CORS.
- Pydantic contract validation, JSON schemas, and generated frontend types.
- `MovementAnalyzer` protocol, injected into the live route through `get_analyzer()`.
- `PoseProvider` and `PoseSequence` video adapter boundary.
- Push-up and squat profiles/counters; planned lunge and gym exercise entries.
- Push-up/squat pose-to-response analyzer; upload 501, local coach.
- Tests for routes, invalid requests, fixture semantics, and deterministic score arithmetic.

Geometry/visibility, median smoothing, and both counters are connected to the live API.
The optional local CV adapter is available (apps/api/VIDEO_SETUP.md). There is no form scorer,
HTTP upload processing, or OpenAI call yet. Authored fixture angles are not video measurements.

## Current work order

| Checkpoint | Work | Priority |
| --- | --- | --- |
| Completed | Geometry, visibility, shared phase/rep segmentation, live API | Foundation |
| Completed | Optional video extraction, push-up counts and cumulative HTTP replay on four real clips | Recorded demo evidence |
| Next | HTTP upload integration, input limits, cleanup/error tests, processing-time check | Critical |
| Then | Coordinate upload loading/timeout, measured results, and video seeking with B | Critical |
| Then | Supported push-up measurements, documented scoring, grounded issues, tests | Critical to form feedback |
| Later | Evidence-only OpenAI coach with local failure fallback | Should have |
| Later | Browser tracking, lunge/other exercises | Only after the recorded push-up demo works |
| Stretch | Automatic exercise detection, ghost comparison, custom ML, history | Only if demo is stable |

Computer B owns browser camera extraction and playback. Computer A owns movement
interpretation. Preserve existing squat support, but do not expand it for this demo.
Real 4K processing takes tens of seconds on this Mac; coordinate request timeouts before
connecting B's upload UI. A successful count does not imply that form has been evaluated.

## Measurement acceptance criteria

Implement small geometry helpers and deterministic tests for ordinary angles, degenerate
points, missing/low-confidence landmarks, and aspect ratios. Unknown visibility is not high
confidence. Smooth only sufficiently observed points; do not interpolate over long lost-pose gaps.
Use an explicit phase state machine with hysteresis/time rules to avoid counting jitter as reps.

Implement `MovementAnalyzer.analyze` and return the existing `AnalysisResponse`. Both live
and uploaded pose sequences must call it. Cumulative live batches start at the set's beginning;
replay deterministically rather than accumulating hidden mutable state across requests.
Keep timestamps tied to the source so rep starts and issue highlights align with playback.

For each supported rule, retain the measurement and rule threshold that justify a finding.
Only report knee tracking from a view that supports that inference; side-view knee flexion
does not establish inward knee movement. Return null scores/limitations when evidence is inadequate.
Set `provenance.kind: "measured"` only when actual pose data has been analyzed; remove
`not_implemented` only when the algorithm really exists. A selected hint gets null confidence.

## Video extraction and dependencies

Add CV libraries only in this branch when needed. Choose versions with working wheels for
the team's Python/Macs, test a short local clip, and pin the resulting dependency set.
The adapter maps SDK objects into our 33-slot structure and unmirrored coordinate convention.
Do not put MediaPipe objects inside domain models or duplicate scoring inside video processing.
Define accepted codecs, clip duration/size limits, decode errors, timeouts, and temporary-file
cleanup before enabling uploads. Read upload timestamps from the source; variable frame rate
must not silently become frameIndex divided by an assumed fps.

No video should be committed. Keep consented recordings in an ignored local folder and
share them through an agreed private channel. No training a pose model from scratch.

## Checks and handoff to B

From `apps/api`, with `.venv` active:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -c 'from app.main import app; print(app.title)'
```

Success prints passing tests and `FormCoach API`. From the repo root, run the schema check:

```bash
apps/api/.venv/bin/python scripts/export_contracts.py --check
```

New algorithms should fit the contract without schema changes. If a change is unavoidable,
follow contracts/README.md and coordinate regenerated frontend types. Send B the capability,
example response, limitations, and small commit to integrate. Keep unrelated UI edits out of this branch.
