# FormCoach agent context

## Project and stopping point

FormCoach is a movement/fitness coaching demo for UBC BizTech HelloHacks 2026. Two beginner
developers have roughly a tomorrow-scale hackathon timeline. Prioritize a reliable live
squat demo, clear evidence, and a polished presentation. Judging: functionality 35%, pitch
25%, technical complexity 20%, UX/design 20%.

The bootstrap task ends with a verified shared foundation on main. Do not implement the
full product during bootstrap. Feature work begins after humans create their branches.
Future agents should implement the responsibilities in their handoff, not restart the design.

## Read before coding

1. README.md and docs/ARCHITECTURE.md.
2. docs/API_CONTRACT.md, contracts/README.md, and docs/DECISIONS.md.
3. Your docs/BACKEND_HANDOFF.md or docs/FRONTEND_HANDOFF.md.
4. docs/PRODUCT_SCOPE.md, docs/TASKS.md, and docs/SAFETY.md.
5. Backend measurement work: docs/EXERCISE_SYSTEM.md and docs/SCORING.md.
6. Coaching work: docs/AI_COACH.md.

## Settled architecture

- Monorepo; independent Next.js/TypeScript frontend and FastAPI/Pydantic Python backend.
- Browser live pose extraction and backend uploaded-video extraction both produce our
  normalized `PoseFrame` representation. Analysis never depends on MediaPipe objects.
- Pretrained pose estimation later; no training a pose model from scratch.
- `MovementAnalyzer` is the shared interface for rules and possible later lightweight ML.
- Version `1.0` JSON contract; Python models -> checked-in schemas -> generated TS types.
- Stateless cumulative HTTP batches first. No database or WebSocket requirement.
- AI explains measured evidence. It cannot invent detections, diagnose, or predict injury.
- Bootstrap fallback never calls OpenAI. Mock JSON is explicitly synthetic.

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

Health works. Live squat analysis derives completed reps, timestamps, and smoothed 2D knee
angles from cumulative poses; insufficient observations return null counts. Other hints or no
hint remain `not_implemented`. Scores stay null. Upload returns 501; coach uses a local fallback.
Frontend foundation renders the six-rep fixture and can check health. No pose model or real
scorer is integrated. Next: browser pose integration and real-camera validation with Computer B.
Read apps/api/README.md checkpoint 3 for side selection, tracking loss, and finalization limits.
