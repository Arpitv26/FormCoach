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
video analysis focus, plus incline dumbbell bench press, cable lateral raises, lat pulldowns,
and triceps pushdowns for gym sessions. Squats are out of the current demo scope.
Control+C stops the server. Copy settings once; later runs only need `npm run dev`.
The backend is optional until integration. No API key or Python is needed for camera preview.

## Push-up video analysis

Choose **Analyze a push-up video** on the home page, or open `/upload`.
Record a short side-view set of 3–5 push-ups with the whole body visible, transfer
it from your phone to this computer, and choose the clip. Preview stays local until
**Analyze push-ups** sends multipart `file` and `exerciseHint=push-up` to the API.
Supported file extensions: MP4, MOV, WebM; maximum 250 MiB, 120 seconds, 4K total
pixels and 4096 pixels on either axis. The server validates the actual video.

Real analysis requires Computer A's updated `backend-cv` server with video dependencies
and its pose model installed. Ask A to follow `apps/api/VIDEO_SETUP.md` and
`apps/api/HTTP_UPLOAD.md` on that branch. The bootstrap API on this frontend branch
still returns 501; the UI explains that analysis is unavailable, with no demo fallback.
No backend or shared-contract changes are included in this frontend increment.
Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` to that server (normally
`http://localhost:8000`), allow the frontend origin in backend CORS, then restart
`npm run dev` from `apps/web`. The public URL must be reachable by the browser.

Uploads have a 240-second client timeout; other requests retain 15 seconds.
There is no automatic retry. **Stop waiting**, changing clips, and leaving the route
abort the client request; native server processing may continue. Wait before retrying.
The UI reports setup-required, busy, timeout, invalid-video, network, and legacy errors.

Expected success: a final response with counted reps, timing, observed elbow angles,
and visibility limitations. Partial means incomplete evidence, not ongoing processing.
Null scores stay unavailable. **View at …** and key-moment buttons seek within the same
local clip, only for measured upload responses. If the browser cannot play a phone codec,
analysis can still be attempted, but seeking is disabled. For playback, export H.264 MP4
and analyze that exact export so timestamps match. No skeleton overlay is fabricated.
Local video URLs are released on replacement, removal, or leaving the route.

Before the integration PR, verify a real push-up clip against A's configured server,
including rep timestamps and a clip with insufficient visible evidence. Frontend tests
use controlled responses; they do not verify pose estimation or counting accuracy.
Never commit clips, `.env.local`, or generated build output.

## Camera and exercise setup

Choose **Use camera**, or **Preview framing** on a gym exercise. `/camera` defaults
to push-ups; `/camera?exercise=lat-pulldown` is an example of a specific selection.
Click **Enable camera** and allow access. The mirrored preview uses no microphone,
recording, or upload. **Stop camera**, leaving the page, and changing exercises release
the camera tracks. Permission granted after cancellation is immediately released too.
Open the app on localhost or HTTPS for browser camera access.

The camera screen is preview-only: it does not detect pose readiness, count reps, or score movement.
Push-ups use the existing `push-up` backend hint. The four gym slugs in
`src/lib/exercises.ts` are frontend routing identifiers and have `backendHint: null`.
Do not send them to the API until Computer A registers their agreed exercise IDs and
coordinates supported views and response examples. Push-ups replace squats as the
first analysis target; gym views still require validation.

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
