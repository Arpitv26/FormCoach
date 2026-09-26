# FormCoach API — Computer A

Read [AGENTS.md](../../AGENTS.md), [backend handoff](../../docs/BACKEND_HANDOFF.md), and
[beginner setup](../../docs/BEGINNER_SETUP.md). Python 3.12 is the team default.

From this folder (`apps/api`):

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Create the environment and copy settings once. On later runs, activate it and start Uvicorn.
Open http://localhost:8000/api/v1/health or http://localhost:8000/docs. Control+C stops it.
No API key is required. The health response is `{"status":"ok","service":"formcoach-api"}`.

| Folder | Responsibility |
| --- | --- |
| `app/api/routes` | HTTP validation, routing, status codes |
| `app/core` | Local settings and CORS |
| `app/domain` | Stable v1.0 JSON types and semantic validation |
| `app/analysis` | Geometry, visibility, push-up/squat segmentation and analyzer; future scoring |
| `app/analysis/exercises` | Example/planned configuration profiles |
| `app/services` | Optional MediaPipe/video adapters; local coach fallback |
| `tests` | Route, validation, fixture, and score arithmetic checks |

Pose analysis counts push-up and squat reps from supplied poses. Other hints (or no hint) return
`not_implemented`. Upload uses optional local CV extraction. Coach remains local. Follow
[HTTP_UPLOAD.md](HTTP_UPLOAD.md) to test the endpoint and hand it off to Computer B.

## Feature checkpoint 1: joint angles and landmark visibility

`app/analysis/geometry.py` now measures 2D angles. `measure_joint_angle` takes a `PoseFrame`,
three canonical joint names (the middle name is the angle's vertex), image dimensions,
and an explicit visibility threshold such as `SQUAT_PROFILE.minimum_visibility`.
It converts normalized coordinates back to equal-scale image axes before calculating.
The result is an internal `AngleMeasurement`, not an additional public API response.

`app/analysis/visibility.py` checks only the requested joints. Missing joints, estimates outside
the image, unknown visibility, and visibility below the supplied threshold block measurement.
The helper reports each blocked joint and its reason. Undefined geometry, such as a hip
at exactly the same image position as its knee, also returns `angle_deg=None` with a reason.
A visibility check passing does not establish a suitable camera view or correct movement.
Depth is unused: these are image-plane angles, not calibrated 3D measurements.

These helpers are tested building blocks used by the live endpoint through the analyzer.
No new packages or API keys are needed.

To try the math, run these from `apps/api` with the existing virtual environment:

```bash
source .venv/bin/activate
python -c 'from app.analysis.geometry import angle_degrees; print(angle_degrees((1, 0), (0, 0), (0, 1)))'
python -m pytest -q tests/test_geometry.py tests/test_visibility.py
```

The first command activates the project's Python environment. The second prints `90.0`:
the three points form a right angle. The tests should show **57 passed**. They cover known
angles, image aspect ratios, missing/hidden/outside landmarks, and invalid configuration.

## Feature checkpoint 2: squat rep counting

`app/analysis/exercises/squat_segmentation.py` supplies `segment_squats`. It consumes a
chronological sequence of `AngleSample(timestamp_ms, angle_deg)` values from one knee.
Use the geometry helper's output; keep the same anatomical side throughout a set, and
send `None` when a required joint is unusable. Do not switch knees to bridge lost tracking.
The result contains completed rep segments, the current phase, the latest smoothed angle,
and the number of tracking breaks. These are internal types; the public API is unchanged.

The counter must observe standing before it can follow descent -> bottom -> ascent ->
standing and count a rep. The initial policy only counts cycles reaching the configured
bottom threshold: shallow attempts are not counted yet. This is a limitation of the
provisional segmentation policy, not a judgment about correct squat depth.

| Setting | Initial heuristic |
| --- | --- |
| Standing / bottom knee angles | At least 160 degrees / at most 100 degrees, from the squat profile |
| Separate transition thresholds | Begin descent at 150 degrees or less; leave bottom at 110 or more |
| Stable transition | Condition must hold for at least 150 ms across consecutive usable samples |
| Smoothing | Median of the most recent 3 usable angle samples; wait for a full window after reset |
| Completed-rep duration | At least 800 ms; unfinished attempts expire after 15000 ms |
| Tracking gaps | More than 300 ms between samples resets readiness and any unfinished rep |
| Missing angle | Any `None` resets immediately, even for a short dropout; completed reps are retained |

These heuristics need real-camera calibration. The three-sample median depends on sampling
rate, and smoothing/confirmation add latency. No missing poses are interpolated. Start is
the first sample of a confirmed descent; end is the sample confirming standing. The bottom
timestamp is the earliest lowest smoothed angle observed after descent confirmation, not
an independently verified anatomical bottom. All times use the original sample clock.

Replay the complete cumulative set on every call. Returned reps replace the prior result;
do not add the latest count to the previous count. A final snapshot never completes an
unfinished rep automatically. Checkpoint 3 below connects this counter to the live route.

Run the focused tests from `apps/api`, with `.venv` active:

```bash
python -m pytest -q tests/test_squat_segmentation.py
```

Expect **43 passed**. The tests use synthetic angle sequences and known synthetic body
landmarks; no real-camera accuracy has been established yet.

## Feature checkpoint 3: live API integration

`app/analysis/movement.py` implements `MovementAnalyzer`. The live route now selects
`RuleBasedAnalyzer`, which measures the supplied poses and replays the selected push-up or squat counter.
No contract fields, schemas, frontend files, or dependencies changed.

The joint names and standing-phase details below describe the original squat path.
See **Push-up priority** below for its elbow measurements and top-position equivalent.

- Send `exerciseHint: "push-up"` for the demo or `"squat"` for the legacy counter.
  No hint or another registered exercise remains unimplemented.
- The first usable hip-knee-ankle triplet selects the side; left wins if both work in that
  frame. Keep this side throughout the set, including during tracking loss. Visibility must
  be at least 0.7 for each joint. Coordinates must be in-frame, with non-degenerate geometry.
- Completed reps include start/end timestamps, `durationMs`, and either
  `minSmoothedLeftKneeAngleDeg` or `minSmoothedRightKneeAngleDeg`. The minimum is from the
  causal smoothed signal after descent confirmation. It is not a raw-sample minimum.
- The `minimum_knee_angle` key moment and timeline refer to this smoothed minimum, not a
  verified anatomical bottom. Scores, confidence, full-body visibility, and scoring remain null.
- Before stable standing is observed, count is null and status is `insufficient_data`.
  Once ready, zero means no completed cycles observed. During a set, status is `partial`.
  A final snapshot is `complete` only when standing with no unavailable frames/tracking breaks.
  Final interrupted sets remain `partial`; read `limitations`, even after Stop.
- `provenance.kind: "measured"` means the algorithm ran on supplied poses. The server cannot
  verify they came from a camera. Synthetic test inputs must still be presented as synthetic.
- Squat real-camera accuracy is still unverified. Use a
  side view, keep one whole leg visible, and stand still briefly before and after each set.

From `apps/api`, with `.venv` active:

```bash
python -m pytest -q tests/test_live_analysis.py
```

The tests send synthetic body landmarks through real HTTP route handling. They cover known
angles/times, cumulative replay, side locking, visibility failures, gaps, finalization,
unchanged JSON Schema, and coach compatibility. No camera or API key is needed.

To inspect a request manually, start the API using the commands at the top of this document,
open http://localhost:8000/docs, expand **POST /api/v1/live/analyze-batch**, and click
**Try it out**. Paste `contracts/examples/live-pose-batch.json` into the request box and click
**Execute**. Expect HTTP 200 with `status: "insufficient_data"` and `totalReps: null`: that tiny
two-frame example deliberately has too little data to count a rep. It never returns demo reps.

## Push-up priority

The user changed the demo to **prerecorded push-ups**, with no squat demo. Select
`exerciseHint: "push-up"`. The earlier squat implementation is retained for compatibility.
`pushup_segmentation.py` uses the shared `angle_segmentation.py` engine. The original squat
tests protect that extraction from regressions.

The push-up counter measures shoulder-elbow-wrist angle on one locked side. It first requires
the straight-arm top position (at least 160 degrees), confirmed descent, flexion at most
100 degrees, ascent, and return to the top. Other smoothing/timing/gap settings match the
checkpoint 2 table. These are provisional counting thresholds, not a correct-depth standard.
Shallow attempts do not count yet. Body alignment, camera orientation, and actual exercise
identity are not inferred; a selected exercise is not automatic recognition.

Results use `minSmoothedLeftElbowAngleDeg` or `minSmoothedRightElbowAngleDeg`, `durationMs`,
and a `minimum_elbow_angle` key moment. Scores remain null. Finalization uses the top position
instead of standing. Null/confidence/tracking-loss behavior follows checkpoint 3.

## Remaining backend plan

Checkpoint 4 preparation now includes a [capture replay tool and step-by-step guide](examples/README.md).
It tests saved poses against a running API, compares a human count, and checks cumulative
response stability. A labeled synthetic example is included. Four actual MOV recordings
now match the human counts of 3, 1, 1, and 2; see [VALIDATION.md](VALIDATION.md) for
evidence, the short-clip timing fix, repeat commands, and limits of this check.

1. Completed: geometry and visibility helpers.
2. Completed: conservative squat segmentation, smoothing, and failure-case tests.
3. Completed: connect measured poses and completed reps to the existing live API contract.
4. Completed: push-up elbow counting and capture replay checker, tested with synthetic inputs.
5. Completed: local video extraction and count/sequence review on four actual recordings.
6. Completed: HTTP upload integration, cleanup/error tests. Next: frontend playback/timeout coordination.
7. Descriptive elbow excursion/timing implemented ([MEASUREMENTS.md](MEASUREMENTS.md)); next compare reps and establish grounded rules before scoring.
8. Add evidence-only coaching. Browser tracking follows when Computer B is ready.

The local recorded-video adapter is now available: follow [VIDEO_SETUP.md](VIDEO_SETUP.md).
It uses optional pinned MediaPipe/OpenCV packages, writes poses and upload analysis locally,
and powers the HTTP upload route described in [HTTP_UPLOAD.md](HTTP_UPLOAD.md). Actual-footage
counts are checked; UI seeking accuracy and broader counting reliability remain to be tested.

Keep each checkpoint small: implement, test, review, commit, and push `backend-cv`.

## Backend checks

With `.venv` active:

```bash
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -c 'from app.main import app; print(app.title)'
```

To format your Python edits, use `python -m ruff format .`. To regenerate contracts from
the repository root, follow [contracts/README.md](../../contracts/README.md).

`requirements.txt` pins runtime packages; `requirements-dev.txt` adds testing/linting.
The `.in` files list direct dependencies and intended ranges. When adding a package,
update the appropriate `.in` and pinned `.txt` file in the same commit, run `python -m pip check`,
and test a fresh environment. Do not replace the lock with an unrelated global `pip freeze`.
Current Starlette may emit a test-client deprecation warning about httpx; existing route tests
pass with the pinned compatibility path. Review the adapter before future dependency upgrades.
