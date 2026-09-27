# Task board

Ownership: **[A]** backend/CV/ML/AI · **[B]** frontend/product/UX · **[SHARED]** agree together.
Keep feature work in the app folder you own. The bootstrap stops after the foundation; the
remaining checkboxes are the next agents' backlog, not work to finish in the initial commit.

**Current order and acceptance criteria:** [NEXT_STEPS.md](NEXT_STEPS.md).
B is finishing coach interactions, comparisons, results polish, live counting and demo
verification. A continues backend work, then owns the visual overhaul after B's PR is
reviewed and integrated. PRs #1/#2/#3 are already merged into main `79f8da3`.

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
- [x] [A] Descriptive per-rep elbow excursion and timing parts; see apps/api/MEASUREMENTS.md.
- [x] [A] Causal within-set timing/range comparisons with traceable review flags and synthetic positive cases.
- [ ] [A] Validate a real positive comparison case; do not infer positive-case accuracy from current unflagged clips.
- [ ] [A] Improve measured tracking coverage and actionable missing-joint feedback.
- [ ] [A] Implement and validate one side-view body-alignment measurement before deriving a cue.
- [ ] [A] Justified score formulas only after evidence/view/calibration review.
- [x] [A] Counter/API tests for occlusion, missing joints, jitter, timing gaps, and partial reps.
- [ ] [A] Extend those failure-case tests to future form metrics and scoring.
- [x] [A] Push-up elbow cycle counter and shared segmentation mechanics (synthetic tests).
- [x] [A] Saved-pose replay checker and labeled synthetic push-up capture.
- [ ] [A] Lunge analyzer only after the push-up video demo works.
- [x] [A] Optional local video decoding + MediaPipe pose adapter + bounded inputs and cleanup.
- [x] [A] Integrate validated video processing into HTTP uploads, including cleanup/errors and busy handling.
- [x] [B] Use separate 240-second upload timeout and connect measured results/playback (PR #1; one real-clip UI check passes).
- [x] [A] Phase 5: Optional OpenAI evidence selector, useful local fallback, evidence/uncertainty tests.
- [x] [A] Verify one live OpenAI request with a locally configured key (2026-09-26: synthetic rep-3 timing QA, provider openai, 3.22 seconds).
- [ ] [SHARED] Recheck frontend branch periodically; see INTEGRATION_STATUS.md for current gaps.
- [ ] [A] Phase 6: optional automatic exercise classification.
- [ ] [A] Phase 7: advanced ML/reference features only if demo is stable.

## FRONTEND

- [x] [B] Initial landing/demo interface and responsive visual direction.
- [x] [B] Uploaded results with actual measurements, null and error states.
- [x] [B] Camera permission, framing guidance, exercise selector (automatic readiness remains unavailable).
- [x] [B] Upload selection/preview and honest loading/error states (PR #1).
- [x] [A, authorized by user] Browser pose adapter and correctly mirrored skeleton overlay; simulated-camera verified, physical check pending (POSE_OVERLAY.md).
- [x] [A, authorized by user] Uploaded pose-track endpoint and synchronized landscape/portrait playback overlay.
- [ ] [B] Cumulative live requests, session reset/finalization, response replacement.
- [x] [B] Per-rep measurement cards and synchronized rep/minimum-angle jumps.
- [ ] [B] Rep comparison presentation, graphs and issue navigation; scores remain null.
- [ ] [A, later] Worst-form rep ranking only after justified scoring exists.
- [ ] [B] Coach panel and visible provider/confidence/limitations.
- [ ] [B] Accessibility, transitions, small-screen layout, demo polish.
- [ ] [SHARED] Review and integrate B's completed feature PR; transfer UI ownership.
- [ ] [A, after handoff] Full frontend visual overhaul, preserving tested analysis/overlay behavior.

## INTEGRATION

- [x] [SHARED] Both computers branch from the same published bootstrap main commit.
- [x] [SHARED] Browser MediaPipe Lite and side-view push-up demo selected.
- [ ] [SHARED] Confirm identical coordinates/timestamps in browser and video adapters.
- [x] [SHARED] Connect real push-up upload responses without dashboard-specific shape changes.
- [ ] [SHARED] Test live reset, final snapshot, camera loss, backend down, and stale responses.
- [ ] [SHARED] Ensure synthetic/placeholder results are never presented as measured.
- [x] [SHARED] Validate rep-start and minimum-angle playback on IMG_6939 (0.733 s / 1.733 s).
- [ ] [SHARED] Validate playback of a real comparison flag when suitable footage exists.
- [x] [SHARED] Merge backend and overlay contract changes into main (PRs #2/#3).
- [ ] [SHARED] Run all checks on B's upcoming integrated feature commit.

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
