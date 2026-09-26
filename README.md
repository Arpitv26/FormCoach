# FormCoach

UBC BizTech HelloHacks 2026 · A camera-based movement coach grounded in measured evidence.

**FormCoach is in development.** The frontend/backend foundation, shared data formats,
legacy mock squat results, and tested push-up counting from supplied poses are ready.
Local video pose extraction and evidence-based coaching are available; browser pose tracking
and form scoring remain unfinished. Coaching works locally; optional OpenAI evidence selection
has mocked API tests and one successful live timing-question check. See [video setup](apps/api/VIDEO_SETUP.md)
and [coach setup](apps/api/COACH_SETUP.md).
No API key, database, Docker, or GPU is needed to run this foundation.

## How it works

Our goal is to turn an ordinary camera into a movement coach. A user performs an exercise,
and FormCoach will count repetitions, measure how they move, and explain their results.
Our demo priority is **push-ups in prerecorded gym video**. Backend video pose extraction
works locally and through HTTP upload; browser tracking is a later integration. This diagram shows the complete vision:

```text
       LIVE WEBCAM                      UPLOADED VIDEO
            |                                |
   Pose model in browser             Pose model on backend
            |                                |
            +----------------+---------------+
                             |
                             v
              BODY LANDMARKS (shared format)
              Joint positions + timestamps
                             |
                             v
              OUR MOVEMENT ANALYSIS (Python)
              - Check which joints are visible
              - Calculate joint angles
              - Track movement phases
              - Count completed repetitions
              - Measure and compare each rep
                             |
                             v
                    STRUCTURED RESULTS
              Measurements, scores, issues,
                  and video timestamps
                             |
               +-------------+-------------+
               |                           |
               v                           v
        RESULTS DASHBOARD              AI COACH
        Graphs, rep breakdown,         Explains only the
        and video highlights           supplied evidence
               ^                           |
               +---------------------------+
```

### What we use and what we build

- **Existing pose model:** Our local video adapter uses Google's
  [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker),
  which estimates 33 body landmarks, including hips, knees, and ankles. It is already
  trained to locate body parts; we do not need to train a pose model from scratch.
- **Our analysis code:** We turn those joint positions into angles, repetitions, timing,
  and explainable exercise feedback. We start with mathematical rules that we can test.
  For example, following the shoulder-elbow-wrist angle helps identify a push-up's
  downward movement and return to the straight-arm top position.
- **AI coach:** The backend builds short explanations from measured results. Optional OpenAI
  selects relevant evidence, and the server renders checked wording. Unknown scores stay
  unknown, and camera limitations remain visible. No key is required for the local coach.

The same movement-analysis code will handle live and uploaded video because both paths
produce the same joint-position format. Our main contribution is this analysis layer and
the interface that makes its results understandable.

### How the two computers work together

**Computer A (us)** builds the Python backend: movement measurements, rep counting,
video processing, and AI coaching. **Computer B** builds the Next.js frontend: camera
experience, skeleton overlay, dashboard, and visual polish. Shared data formats let both
people work independently; the frontend can use clearly labeled mock results until real
analysis is ready.

## Start here

- New to coding? Follow [Beginner setup](docs/BEGINNER_SETUP.md), one command at a time.
- Computer A / backend agent: read [AGENTS.md](AGENTS.md), then [Backend handoff](docs/BACKEND_HANDOFF.md).
- Computer B / frontend agent: read [AGENTS.md](AGENTS.md), then [Frontend handoff](docs/FRONTEND_HANDOFF.md).
- Before branching: read [Git workflow](docs/GIT_WORKFLOW.md).
- Current A/B alignment: [Integration checkpoint](docs/INTEGRATION_STATUS.md).

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

| Endpoint | Current behavior |
| --- | --- |
| `GET /api/v1/health` | Returns `{"status":"ok","service":"formcoach-api"}` |
| `POST /api/v1/live/analyze-batch` | Counts selected push-up/squat cycles from supplied poses; per-rep times and joint angles; scores remain null |
| `POST /api/v1/videos/analyze` | Analyzes selected push-up/squat video through optional local CV; returns measured analysis |
| `POST /api/v1/coach` | Local measured-evidence summary; optional OpenAI evidence selection with explicit opt-in |

Mock results are labeled **MOCK DEMO DATA**. Select `push-up` for the intended demo exercise.
The earlier squat counter still works; other profiles remain unimplemented. The original squat
mock is a legacy UI fixture, not the demo plan. A local MediaPipe video adapter is available; browser tracking is not integrated yet.

Backend helpers now measure 2D joint angles, check visibility, and count completed exercise
cycles through the live API. Synthetic tests cover partial reps, jitter, tracking loss,
and repeatable live-batch replay. Four actual MOV recordings now match human counts of
**3, 1, 1, and 2 push-ups**, after fixing a phase-confirmation timing bug. This checks those
clips, not general form accuracy. See the [recording validation report](apps/api/VALIDATION.md).
HTTP upload is now wired. Next is matching playback in the frontend; Computer B must also
set a separate upload timeout. See the [upload guide](apps/api/HTTP_UPLOAD.md).
Push-up reps also expose observed elbow range and timing around the minimum angle; see
[measurement definitions](apps/api/MEASUREMENTS.md). Scores remain unavailable.
The frontend can integrate later using `contracts/examples/pushup-analysis.json`, an
explicitly synthetic one-rep fixture with the new fields. Causal timing/range comparisons
also flag measured differences for review; see [comparison rules](apps/api/COMPARISONS.md).
A separate synthetic three-rep comparison fixture demonstrates those flags without claiming
that the user recordings contain them.
See the [backend progress and plan](apps/api/README.md#remaining-backend-plan).

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
