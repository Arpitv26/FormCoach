# Task board

Ownership: **[A]** backend/CV/ML/AI · **[B]** frontend/product/UX · **[SHARED]** agree together.
Keep feature work in the app folder you own. The bootstrap stops after the foundation; the
remaining checkboxes are the next agents' backlog, not work to finish in the initial commit.

## BOOTSTRAP

- [x] [SHARED] Monorepo structure, root agent context, ownership boundaries.
- [x] [SHARED] v1.0 schemas, pose convention, analysis/coach/live/upload contracts.
- [x] [SHARED] Six-rep synthetic squat fixture and live batch example.
- [x] [A] Runnable FastAPI, health, explicit analysis/upload stubs, local coach fallback.
- [x] [A] Replaceable analyzer/provider/coach interfaces and exercise profiles.
- [x] [B] Runnable minimal Next.js page, generated types, centralized API client.
- [x] [SHARED] Beginner setup, handoff docs, scope, safety, demo, decisions, Git guide.
- [x] [SHARED] Python/frontend checks and CI skeleton.

## BACKEND

**Current priority: prerecorded push-ups. No squat demo.**

- [x] [A] Phase 1: aspect-ratio-aware geometry, visibility checks, smoothing.
- [x] [A] Phase 1: squat phase transitions and completed-rep segmentation (synthetic tests).
- [x] [A] Connect the internal squat counter to live API responses without changing the contract.
- [x] [A] Compare four real clips with human counts and visual sequences; counts 3/1/1/2 and HTTP replay pass (apps/api/VALIDATION.md).
- [ ] [SHARED] Validate exact playback alignment and rehearse the integrated demo.
- [ ] [A] Measured push-up metrics, documented score formulas, grounded issues.
- [x] [A] Counter/API tests for occlusion, missing joints, jitter, timing gaps, and partial reps.
- [ ] [A] Extend those failure-case tests to future form metrics and scoring.
- [x] [A] Push-up elbow cycle counter and shared segmentation mechanics (synthetic tests).
- [x] [A] Saved-pose replay checker and labeled synthetic push-up capture.
- [ ] [A] Lunge analyzer only after the push-up video demo works.
- [x] [A] Optional local video decoding + MediaPipe pose adapter + bounded inputs and cleanup.
- [x] [A] Integrate validated video processing into HTTP uploads, including cleanup/errors and busy handling.
- [ ] [B] Use separate 240-second upload timeout and connect measured results/playback (apps/api/HTTP_UPLOAD.md).
- [ ] [A] Phase 5: OpenAI adapter and evidence/uncertainty guardrails.
- [ ] [A] Phase 6: optional automatic exercise classification.
- [ ] [A] Phase 7: advanced ML/reference features only if demo is stable.

## FRONTEND

- [ ] [B] Landing/demo interface and responsive visual direction.
- [ ] [B] Results dashboard entirely from canonical mock; null and error states.
- [ ] [B] Camera permission, framing/readiness states, exercise selector.
- [ ] [B] Upload selection/preview and honest loading/error states.
- [ ] [B] Browser pose adapter and correctly mirrored skeleton overlay.
- [ ] [B] Cumulative live requests, session reset/finalization, response replacement.
- [ ] [B] Per-rep cards, metric graphs, issue timeline, lowest-score highlight.
- [ ] [B] Worst-rep jump against synchronized video.
- [ ] [B] Coach panel and visible provider/confidence/limitations.
- [ ] [B] Accessibility, transitions, small-screen layout, demo polish.

## INTEGRATION

- [ ] [SHARED] Both computers branch from the same published bootstrap main commit.
- [ ] [SHARED] Agree on browser pose provider and first supported camera view.
- [ ] [SHARED] Confirm identical coordinates/timestamps in browser and video adapters.
- [ ] [SHARED] Connect real push-up upload responses without dashboard-specific shape changes.
- [ ] [SHARED] Test live reset, final snapshot, camera loss, backend down, and stale responses.
- [ ] [SHARED] Ensure synthetic/placeholder results are never presented as measured.
- [ ] [SHARED] Validate per-rep/video/issue timestamp alignment with a matching clip.
- [ ] [SHARED] Merge shared contract changes first; all checks pass on integrated main.

## DEMO

- [ ] [SHARED] Choose one reliable exercise/view/rule and a comfortable visible variation.
- [ ] [SHARED] Record consented backup clip; follow gym filming rules.
- [ ] [SHARED] Rehearse live and recorded paths with actual integrated results.
- [ ] [SHARED] Prepare truthful synthetic fallback label and explanation.
- [ ] [SHARED] Rehearse concise pitch tied to judging weights.
- [ ] [SHARED] Freeze dependencies/contracts before presentation.

## DEVPOST

- [ ] [SHARED] Explain the problem, target user, and demonstrated capability.
- [ ] [SHARED] Credit pretrained pose model and describe our custom analysis contribution.
- [ ] [SHARED] Describe evidence-only AI, uncertainty, and scope honestly.
- [ ] [SHARED] Add screenshots and a short demo recording with participant consent.
- [ ] [SHARED] Verify repository/demo links and setup instructions from a fresh checkout.
- [ ] [SHARED] Submit before the event deadline; confirm the actual deadline with organizers.
