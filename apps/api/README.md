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
| `app/analysis` | Geometry and visibility helpers; analyzer placeholder; future rep/scoring helpers |
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
