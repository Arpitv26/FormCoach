# FormCoach web — Computer B

Read [AGENTS.md](../../AGENTS.md), [frontend handoff](../../docs/FRONTEND_HANDOFF.md), and
[beginner setup](../../docs/BEGINNER_SETUP.md). Use Node 24.

From this folder (`apps/web`):

```bash
npm ci
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. Success is an exercise selection page with push-ups as the
live demo focus, plus incline dumbbell bench press, cable lateral raises, lat pulldowns,
and triceps pushdowns for gym sessions. Squats are out of the current demo scope.
Control+C stops the server. Copy settings once; later runs only need `npm run dev`.
The backend is optional until integration. No API key or Python is needed for camera preview.

## Camera and exercise setup

Choose **Set up push-ups**, or **Preview framing** on a gym exercise. `/camera` defaults
to push-ups; `/camera?exercise=lat-pulldown` is an example of a specific selection.
Click **Enable camera** and allow access. The mirrored preview uses no microphone,
recording, or upload. **Stop camera**, leaving the page, and changing exercises release
the camera tracks. Permission granted after cancellation is immediately released too.
Open the app on localhost or HTTPS for browser camera access.

This is preview-only: there is no pose readiness detection, rep counting, or scoring yet.
Push-ups use the existing `push-up` backend hint. The four gym slugs in
`src/lib/exercises.ts` are frontend routing identifiers and have `backendHint: null`.
Do not send them to the API until Computer A registers their agreed exercise IDs and
coordinates supported views and response examples. Push-ups replace squats as the
first live integration target; gym views still require validation.

The existing results component is retained for integration. The canonical synthetic squat
fixture is still used by contract tests; it is not displayed or relabeled as another exercise.

Start with `src/app/page.tsx`. Fetch methods are in `src/lib/api/client.ts`; use
`getMockAnalysis()` in `src/lib/api/mock.ts` to access the canonical shared example.
`src/lib/api/types.ts` is generated; contract changes must be coordinated with A.
Tailwind is installed; the starting CSS is intentionally small and replaceable.

```bash
npm run contracts:check
npm run lint
npm run typecheck
npm test
npm run build
```

For a production preview after a successful build, run `npm start` and open port 3000.
`NEXT_PUBLIC_API_BASE_URL` is read into the frontend build; restart dev or rebuild after changing it.
Never put secrets in a `NEXT_PUBLIC_` variable or this app's source.

ESLint is temporarily pinned to 9.39.5 because the Next.js React plugin failed with 10.11.0
during bootstrap verification. npm may print a support warning. See DECISIONS.md before
upgrading the linter independently of its plugins.

The browser client validates HTTP errors and contractVersion, not every response field at
runtime. Pydantic validates server responses, and frontend tests validate the fixture against
the shared JSON Schema. Add a browser runtime schema validator if a future untrusted external
service makes that necessary; keep it centralized in the API boundary.
