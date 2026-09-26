# Computer A / Computer B integration checkpoint

Checked 2026-09-26 by fetching and reading **origin/frontend at bc6821d**.
This is a code review snapshot, not a claim that the latest UI was launched or demo-tested.
No frontend files were edited or merged into `backend-cv`. Recheck before the next integration
checkpoint; branch heads can advance independently.

## What Computer B has

- Dark fitness UI/results foundation (`59029d7`) and webcam setup/exercise selection (`bc6821d`).
- Push-up uses the correct backend ID `push-up`.
- Gym selection slugs have `backendHint: null`; they are not implemented analyzers.
- Camera is preview/setup only; no recording, pose extraction, or upload request yet.
- Results preserve demo labels and unknown scores. An API client exists for all routes.

## Coordination items — B can do these later

| Item | Backend readiness / frontend action |
| --- | --- |
| Prerecorded push-ups first | User's intended demo remains recorded gym push-ups. Webcam polish is useful but does not replace upload/playback integration. |
| Upload client timeout | Current remote client still uses 15 seconds. Use a separate 240-second timeout for video; keep short calls separate. See apps/api/HTTP_UPLOAD.md. |
| Measured results | Render measurements from MEASUREMENTS.md and COMPARISONS.md; all quality scores still null. Do not require a score to show a completed analysis. |
| Finalized partial results | `partial` can mean a finished upload with incomplete observations, not just a live set in progress. Current results status copy says “Set in progress”; distinguish using source/UI state. |
| Coach | Existing client and v1.0 types work unchanged. Send the actual current analysis, show message + limitations + provider, and allow repeat only on user action. No frontend key. |
| Recorded playback | Keep the local uploaded file for playback and use timestampMs / 1000 for video currentTime. Verify alignment with the exact uploaded recording. |
| Unsupported gym exercises | Keep null backend hints unavailable for real analysis; never relabel a gym exercise as push-up to bypass validation. |

A keeps implementing backend checkpoints independently. B owns apps/web. Neither side needs
to rewrite the other's algorithms. Contract fields and schemas are unchanged in the coaching
checkpoint; coordinate semantics through API_CONTRACT.md and this note.

## What remains before the demo

- A completed one live OpenAI timing-question check on 2026-09-26 (3.22 seconds). Integrated frontend coaching still needs rehearsal.
- A: obtain/validate a real comfortable variation that triggers the comparison rules. Existing
  clips match 3/1/1/2 reps but produce zero review flags. Synthetic positive cases are not proof
  of real-video detection accuracy.
- B: connect upload → measured dashboard → matching playback → coach panel.
- Together: rehearse end to end, including failed uploads, backend down, and fallback coach.
