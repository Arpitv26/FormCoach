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
| `app/analysis` | Analyzer interface and honest placeholder; future math/rep/scoring helpers |
| `app/analysis/exercises` | Example/planned configuration profiles |
| `app/services` | Future pose/video/OpenAI adapters; local coach fallback |
| `tests` | Route, validation, fixture, and score arithmetic checks |

Live analysis returns `not_implemented` with null measurements. Upload returns 501. Coach is
always local in bootstrap. The SDK/CV integrations belong to later backend work.

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
