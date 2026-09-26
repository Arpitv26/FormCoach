# FormCoach web — Computer B

Read [AGENTS.md](../../AGENTS.md), [frontend handoff](../../docs/FRONTEND_HANDOFF.md), and
[beginner setup](../../docs/BEGINNER_SETUP.md). Use Node 24.

From this folder (`apps/web`):

```bash
npm ci
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. Success is a FormCoach page with six clearly labeled mock reps.
Control+C stops the server. Copy settings once; later runs only need `npm run dev`.
The backend is optional until integration. No API key or Python is needed for mock UI work.

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
