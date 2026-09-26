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
| `app/analysis` | Geometry, visibility, and squat segmentation; analyzer placeholder; future scoring |
| `app/analysis/exercises` | Example/planned configuration profiles |
| `app/services` | Future pose/video/OpenAI adapters; local coach fallback |
| `tests` | Route, validation, fixture, and score arithmetic checks |

Live analysis returns `not_implemented` with null measurements. Upload returns 501. Coach is
always local in bootstrap. The SDK/CV integrations belong to later backend work.

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

These helpers are tested building blocks; the live endpoint remains an explicit placeholder
until rep counting and analyzer integration are ready. No new packages or API keys are needed.

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
unfinished rep automatically. The live route is still a placeholder until checkpoint 3.

Run the focused tests from `apps/api`, with `.venv` active:

```bash
python -m pytest -q tests/test_squat_segmentation.py
```

Expect **43 passed**. The tests use synthetic angle sequences and known synthetic body
landmarks; no real-camera accuracy has been established yet.

## Remaining backend plan

1. Completed: geometry and visibility helpers.
2. Completed: conservative squat segmentation, smoothing, and failure-case tests.
3. Next: connect measured poses and completed reps to the existing live API contract.
4. Integrate browser poses with Computer B and compare against visible repetitions in a clip.
5. Add per-rep measurements, supported feedback, and explainable scoring.
6. Add uploaded-video pose extraction through the same analyzer.
7. Add evidence-only OpenAI coaching, then consider additional exercises.

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
