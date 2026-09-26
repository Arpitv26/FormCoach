# Backend / CV / ML / AI handoff — Computer A

Read AGENTS.md, ARCHITECTURE.md, API_CONTRACT.md, EXERCISE_SYSTEM.md, SCORING.md, and SAFETY.md.
Your branch is `backend-cv`; your primary ownership is **apps/api/**. Follow BEGINNER_SETUP.md.
Computer B builds the UI independently from the shared fixture. Preserve its contract.

## What is already wired

- FastAPI health/live/upload/coach routes and CORS.
- Pydantic contract validation, JSON schemas, and generated frontend types.
- `MovementAnalyzer` protocol, injected into the live route through `get_analyzer()`.
- `PoseProvider` and `PoseSequence` video adapter boundary.
- Example squat profile; planned push-up, lunge, and gym exercise entries.
- Explicit placeholder analysis, upload 501 response, local coach fallback.
- Tests for routes, invalid requests, fixture semantics, and deterministic score arithmetic.

There is no actual geometry, smoothing, rep detection, CV model, form scorer, or OpenAI call yet.
Do not mistake example profiles or authored fixture angles for implemented measurement.

## Work order after bootstrap

| Phase | Work | Priority |
| --- | --- | --- |
| 1 | Geometry, aspect-ratio-correct angles, smoothing, visibility gates, squat phase/rep segmentation | Critical |
| 2 | Squat per-rep measurements, documented metrics/weights, grounded issues, summary, tests | Critical |
| 3 | Push-up and lunge rules using the same interfaces | Should have; only after squat works |
| 4 | Uploaded-video extraction with OpenCV and a pretrained pose model | Critical to recorded fallback, after live squat |
| 5 | Evidence-only OpenAI coach with local failure fallback | Should have; use AI_COACH.md |
| 6 | Automatic exercise classification from landmark sequences | Stretch |
| 7 | Ghost comparison, custom lightweight ML, degradation/history/other advanced features | Stretch |

Phases 3–5 can be reprioritized based on the demo; do not delay a reliable squat path to
finish more exercises. Computer B owns browser camera extraction; agree early on a pose provider
and give them a known-valid cumulative sample. Computer A owns all movement interpretation.

## Phase 1 and 2 acceptance criteria

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
