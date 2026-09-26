# Frontend / product / UX handoff — Computer B

Read AGENTS.md, API_CONTRACT.md, ARCHITECTURE.md, and PRODUCT_SCOPE.md first. Your branch
is `frontend`; your primary ownership is **apps/web/**. Follow BEGINNER_SETUP.md to run it.
Do not wait for backend work. No Python or OpenAI key is needed to build the mock interface.

## Starting point

The app is Next.js App Router + TypeScript + Tailwind. The homepage intentionally has only a
FormCoach title, fixture summary, six rep scores, and a health button. You own the detailed design.

| File | Purpose |
| --- | --- |
| `src/app/page.tsx` | Replaceable starting page; currently reads the fixture |
| `src/app/layout.tsx`, `globals.css` | Page frame, metadata, simple styling |
| `src/lib/api/types.ts` | Generated wire types; do not hand-edit |
| `src/lib/api/client.ts` | Central health/live/upload/coach fetch methods and `ApiError` |
| `src/lib/api/mock.ts` | `getMockAnalysis()` returns a fresh copy of the canonical fixture |
| `src/components/backend-status.tsx` | Small client component showing connection/error handling |
| `tests/` | Fixture and API boundary tests; use `npm test` |

Use `contracts/examples/squat-analysis.json` through `getMockAnalysis()`. Build results
components that take an `AnalysisResponse` prop. Later, pass the result of
`api.analyzeLiveBatch(...)` or `api.analyzeVideo(...)` into the same components. Mock mode
must be explicit and labeled; a failed real request must never silently switch to mock data.
The live pose fixture is only a request-shape example, not an animation or squat dataset.

## Responsibilities after bootstrap

1. Create a beautiful, clear landing/demo interface and a responsive layout.
2. Build webcam setup, permission/denied/error states, framing guidance, and exercise selection.
3. Build upload selection, preview, loading, unsupported/unimplemented, and retry states.
4. Build the results dashboard: overall score, five metrics, confidence and unknown states.
5. Add per-rep cards/table, score comparison, issue cards, and timeline markers.
6. Derive worst rep from the lowest available score; add playback jump when matching video exists.
7. Add charts showing scores/metrics across reps; describe changes as form consistency,
   not diagnosed fatigue. Rep 5 is the fixture's low point and rep 6 recovers.
8. Add the coach panel with fallback/provider labeling, concise messages, and limitations.
9. Integrate a browser pose adapter and skeleton overlay once the chosen provider is coordinated.
10. Polish transitions, empty/error states, keyboard access, readable labels, and demo pacing.

Computer A owns rep segmentation, metrics, scoring, and issue detection. Do not duplicate
those algorithms in React. Browser pose extraction is frontend work; agree on provider and
coordinate normalization with A before integrating it. Ordinary camera access requires
localhost or HTTPS. Stop media tracks when leaving the camera page.

## Essential UI states

- Loading, permission denied, no camera, no pose, partially visible, and ready.
- `not_implemented`: explain that the foundation received input but has no real results.
- `insufficient_data`: explain which evidence is missing; do not display zero as a bad score.
- `partial`: show completed reps and limitations. A final set can remain partial after
  tracking loss or an unfinished rep; this status alone does not mean recording is active.
- `complete`: final results; check provenance before calling them measured.
- Nullable values: render “Not available”, not `0`, `NaN`, or a full progress bar.
- Synthetic results: visible “Demo data” label. No pretend processing animation implying real CV.
- API errors: `ApiError.status`/`code` distinguish 501 stub, validation, and connection failure.

## Updated demo priority

The user wants **prerecorded push-ups**, not squats. Prioritize video selection/playback and
push-up results; browser tracking can follow. Send `exerciseHint: "push-up"`. The backend
counts elbow cycles and returns `minSmoothedLeftElbowAngleDeg` or its right-side equivalent,
`durationMs`, and `minimum_elbow_angle` moments, with scores still null. Local video extraction is available on Computer A; real-clip validation and HTTP upload
integration are next. See apps/api/VIDEO_SETUP.md. The old squat mock is a legacy UI fixture, not a push-up analysis; never
relabel its knee measurements or issue as push-up findings. Coordinate a new realistic fixture
when actual push-up metrics exist. Existing v1.0 types need no changes.

The backend replay tool and labeled synthetic elbow capture are documented in
apps/api/examples/README.md. Captured-video validation is still pending.

## Live and playback details

The backend now counts squat cycles from supplied poses, with per-rep time intervals and
smoothed knee-angle measurements. Use `exerciseHint: "squat"`. Scores remain null, so there
is no known worst rep yet. Full-body readiness and camera orientation are not evaluated;
do not show a green full-body indicator based only on a non-null count. See API_CONTRACT.md
for side locking and limitations. The two-frame shared request example produces
`insufficient_data`; it is not enough movement to count a rep. The mock dashboard stays usable.

The v1 live request is a cumulative sampled set, not an incremental chunk. Keep at most
1800 frames / 120 seconds; aim for 15 fps and one POST per second. Only one request in
flight; replace results with each response. Create a new session ID per set; discard old
responses after reset. Send `isFinal: true` at the end. See API_CONTRACT.md before implementing.

Send unmirrored coordinates with image dimensions; mirror the visual overlay and preview
together. Preserve anatomical left/right. Confidence/visibility issues should guide the user
to reposition instead of inventing form feedback.

Playback uses seconds, contract timestamps use milliseconds: divide by 1000. Seek to
`rep.startMs` for the worst-rep jump; later use key moments for precise highlights. The
fixture has no matching video, so mock timeline actions must not imply real synchronized footage.
Live replay requires local recording and a matching time origin; coordinate that feature.

## First useful work package

Build a results screen from the six-rep fixture, including null/error states, before connecting
CV. Then add camera/upload flows. Use one place to select demo data vs real API so integration
does not spread conditional fetch logic throughout the UI.

Run from `apps/web` before committing:

```bash
npm run lint
npm run typecheck
npm test
npm run build
npm run contracts:check
```

Commit frequently with messages such as `feat(web): add mock results dashboard`.
Only edit shared files deliberately; announce needed contract changes to A before relying on them.
