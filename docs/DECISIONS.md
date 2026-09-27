# Architecture decisions

These choices are settled for the hackathon foundation. Change them only for a concrete
demo problem, and record the reason here so future agents do not restart the architecture debate.

| Decision | Why | Consequence |
| --- | --- | --- |
| Prerecorded push-up demo first | User changed the demo away from squats; recorded playback is repeatable | Keep the real upload path reliable while B connects live counting; keep old fixtures honest |
| A takes over visual overhaul after B's feature handoff | B is finishing interactions with limited remaining credits | Review/integrate B's PR first; avoid simultaneous edits to the same frontend screens |
| One monorepo with two apps | Two people can share types/docs while owning separate folders | Avoid edits outside your app without coordination |
| FastAPI + Python + Pydantic | Python is practical for CV/math; FastAPI exposes typed HTTP routes and interactive docs | Backend owns validation and movement interpretation |
| Next.js + TypeScript + Tailwind | Familiar React product tools, typed responses, quick responsive styling | Frontend decides the detailed product design |
| Pretrained pose model | Training pose estimation from scratch is infeasible for tomorrow | Team effort goes into geometry, rep logic, evidence, and UX |
| Our normalized PoseFrame | Keeps movement analysis independent of any SDK/provider | Both pose adapters translate at their boundaries |
| Image dimensions accompany poses | Separate x/y normalization otherwise distorts 2D joint angles | Adapters must preserve orientation, dimensions, and coordinates |
| Same analysis pipeline for live/upload | Avoid conflicting scores and duplicate exercise logic | Extraction differs; MovementAnalyzer is shared |
| Explainable heuristics first | Easier to debug, demonstrate, and validate with a small dataset | Thresholds are labeled uncalibrated; ML can later replace the analyzer |
| OpenAI explains measurements | Natural-language generation should not become invented form detection | Evidence references, uncertainty, and safety rules are mandatory |
| Canonical mock JSON | Frontend must not wait for CV implementation | Components take the same AnalysisResponse in mock and real modes |
| HTTP batching before WebSockets | Simpler debugging, deployment, and failure behavior | Use stateless cumulative snapshots for short sets; measure latency before adding complexity |
| Cumulative snapshots, bounded to 120s/1800 frames | Avoid server state and rep loss at request boundaries | Recompute from the sampled set; replace rather than accumulate responses |
| No DB/auth/queues/cloud requirements | They add setup and integration risk without improving the initial demo | No durable history in bootstrap; history is stretch |
| Nulls plus status/provenance | Prevent fake measurements and misleading empty results | UI must distinguish unknown, synthetic, incomplete, and real results |
| Generated schema and TS types | A frozen boundary must not drift silently across machines | Contract commits regenerate/check all representations |
| Real synchronous uploads after clip validation | Four push-up clips establish a concrete counting checkpoint | Optional local model, worker-thread processing, one extraction per process, explicit errors, no fake fallback |
| Additive upload-with-pose endpoint | Playback needs the exact poses from the same extraction without breaking existing clients | New VideoAnalysisResponse wraps unchanged analysis plus bounded pose track; no server cache |
| Local browser skeleton model | Live joints should render without an API key or video upload | Pin browser library; download Lite model once; mirror only display; live counting is a later integration |
| Coach local by default | No key or spend should be required to run the app | Paid calls need COACH_PROVIDER=openai, SDK, and key; key alone does not enable them |
| OpenAI selects reviewed evidence statements | Structured output alone does not guarantee factual prose | Validate selected IDs, render wording server-side, preserve uncertainty; free-form generation remains deferred |
| Per-app dependencies and env files | Beginners can run one app without installing the other | No root npm workspace; run npm commands from apps/web |
| Node 24, Python 3.12 team defaults | Match both machines and CI with small pinned dependency sets | Create separate local environments; do not share installed dependency folders |
| Explicit ESLint step | Current Next.js builds do not run lint automatically | CI runs lint, typecheck, tests, and build separately |
| ESLint 9.39.5 temporarily pinned | ESLint 10.11.0 crashes in the current Next.js React lint plugin during bootstrap validation | Dev-tool compatibility pin; review once the plugin supports 10; npm may show its support warning |
| Explicit webpack production build | Keeps production compilation on a predictable existing builder for the small bootstrap | Dev still uses Next's default; reconsider only for a concrete need |

Reference behavior checked against the [Next.js installation docs](https://nextjs.org/docs/app/getting-started/installation)
and FastAPI's [multipart](https://fastapi.tiangolo.com/tutorial/request-files/) and
[CORS documentation](https://fastapi.tiangolo.com/tutorial/cors/). OpenAI integration guidance is linked in AI_COACH.md.

No actual analysis support is implied by profile registration. The first product checkpoint is
now a reliable prerecorded push-up demo (user priority change); additional exercises and custom lightweight ML are later decisions.
