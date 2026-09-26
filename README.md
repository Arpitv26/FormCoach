# FormCoach

UBC BizTech HelloHacks 2026 · A camera-based movement coach grounded in measured evidence.

**This is the shared foundation, not a finished movement analyzer.** The Next.js homepage,
FastAPI routes, version 1.0 contracts, synthetic six-rep squat example, checks, and team
handoffs are ready. Real pose estimation, rep counting, and form scoring are next tasks.
No API key, database, Docker, or GPU is needed to run this foundation.

## Start here

- New to coding? Follow [Beginner setup](docs/BEGINNER_SETUP.md), one command at a time.
- Computer A / backend agent: read [AGENTS.md](AGENTS.md), then [Backend handoff](docs/BACKEND_HANDOFF.md).
- Computer B / frontend agent: read [AGENTS.md](AGENTS.md), then [Frontend handoff](docs/FRONTEND_HANDOFF.md).
- Before branching: read [Git workflow](docs/GIT_WORKFLOW.md).

## Run locally

Use Node 24 and Python 3.12. Run these from the repository folder containing this README
and `apps/`. This checkout is inside `helloHacks/helloHacks`, so the outer workspace is
**not** the repository root. On another computer, a normal clone has only one `helloHacks` folder.

Terminal 1 — backend:

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Terminal 2 — frontend, starting from the repository root again:

```bash
cd apps/web
npm ci
cp .env.example .env.local
npm run dev
```

Open [frontend](http://localhost:3000), [API health](http://localhost:8000/api/v1/health),
or [interactive API docs](http://localhost:8000/docs). The homepage uses the shared mock
JSON and works even when the backend is stopped. Click **Check backend health** to test
the connection. Stop each server with **Control+C** in its terminal.

## Repository map

```text
apps/api/       Python API, domain types, replaceable analysis interfaces, tests [A]
apps/web/       Next.js, TypeScript API client, generated types, mock page, tests [B]
contracts/     JSON schemas and canonical examples                            [SHARED]
docs/          Setup, architecture, API, handoffs, scoring, scope, demo         [SHARED]
scripts/       Export/check Python models against shared JSON schemas         [SHARED]
.github/       CI checks for both apps                                        [SHARED]
AGENTS.md      Rules and ownership for future coding agents                   [SHARED]
```

## What works today

| Endpoint | Foundation behavior |
| --- | --- |
| `GET /api/v1/health` | Returns `{"status":"ok","service":"formcoach-api"}` |
| `POST /api/v1/live/analyze-batch` | Validates poses; returns `not_implemented`, null scores, no invented reps |
| `POST /api/v1/videos/analyze` | Accepts the multipart shape; returns HTTP 501 with an explicit placeholder error |
| `POST /api/v1/coach` | Deterministic local fallback; no OpenAI calls, even if a key is set |

Mock results are labeled **MOCK DEMO DATA**. No exercise is analyzed yet. The squat
profile is an example configuration; all other profiles are planned.

## Check your work

From the repository root, after the installs above:

```bash
apps/api/.venv/bin/python -m pytest -q apps/api/tests
apps/api/.venv/bin/python -m ruff check apps/api scripts
apps/api/.venv/bin/python -m ruff format --check apps/api scripts
apps/api/.venv/bin/python scripts/export_contracts.py --check
cd apps/web
npm run contracts:check
npm run lint
npm run typecheck
npm test
npm run build
```

CI runs these checks on pushes and pull requests. Dependency versions are pinned in
the Python requirements files and the frontend lockfile. Do not upgrade them during
integration unless needed to fix a concrete problem.

## Project guide

[Architecture](docs/ARCHITECTURE.md) · [API contract](docs/API_CONTRACT.md) ·
[Exercise system](docs/EXERCISE_SYSTEM.md) · [Scoring](docs/SCORING.md) ·
[AI coach](docs/AI_COACH.md) · [Safety](docs/SAFETY.md) ·
[Scope](docs/PRODUCT_SCOPE.md) · [Demo plan](docs/DEMO_PLAN.md) ·
[Decisions](docs/DECISIONS.md) · [Tasks](docs/TASKS.md)
