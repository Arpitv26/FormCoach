# Remaining work — after backend and overlay integration

Updated 2026-09-26. Integrated baseline: main `79f8da3` (PRs #1, #2 and #3 merged).
This is the current work order. Keep the longer product vision in PRODUCT_SCOPE.md;
do not try to finish every stretch feature before the demo.

## Ownership confirmed by the humans

- **Computer B now:** coach panel/interactions, rep comparisons, results polish, live rep
  counting, and demo verification. These are in progress, not verified delivered features.
- **Computer A now:** backend analysis, validation, reliability and integration support.
  Do not edit B's active frontend components or change their contract unexpectedly.
- **Computer A after B's handoff:** the full frontend visual overhaul. B first commits,
  pushes and opens a PR; A reviews/tests it, integrates it, then takes ownership of web UI.
  B stops editing those screens before the redesign starts. Preserve working behavior/tests.

## What the code actually does today

| Capability | State | Evidence / remaining limitation |
| --- | --- | --- |
| Upload decoding and pretrained pose extraction | Implemented | Four real MOV clips; portrait rotation supported; bounded inputs and cleanup |
| Push-up counting | Implemented | Human counts 3/1/1/2 match; small sample, not a general accuracy benchmark |
| Rep timestamps and elbow measurements | Implemented | Duration, min/max, excursion, time around minimum angle; 2D observations |
| Rep comparisons | Implemented, partly validated | Timing/range changes use two stable prior reps; real clips currently have zero flags; positive cases synthetic |
| Tracking coverage / missing-joint feedback | Implemented | Sample counts and actionable joint reasons; no readiness or quality score |
| Live analysis API | Implemented | Cumulative snapshots, deterministic replay; B is connecting the browser |
| Live / uploaded skeleton | Implemented | Browser and portrait/landscape playback checks; actual webcam smoothness needs recheck |
| Coach API | Implemented | Local summary and optional OpenAI evidence selection; B is building interactions |
| Form score and five quality metric scores | **Missing** | `analysis/scoring.py` is a placeholder; real scores remain null |
| Body-line geometry | Implemented | Median 2D shoulder–hip–ankle angle per rep; seven real-frame checks; not a form assessment |
| Body alignment / depth-quality coaching | **Missing** | A reliable interpretation and corrective cue still need separate validation |
| Full-body visibility / camera orientation | **Missing** | Required-joint visibility is checked, but these session-level judgments stay unknown |
| Worst-form rep ranking | **Missing** | No quality score exists; a flagged change can be reviewed without calling it the worst rep |
| Other gym exercises / automatic recognition | **Missing** | Registered profiles and UI choices do not establish analysis support |

The coach selects reviewed statements from supplied numbers. It does not independently
watch video, generate new findings, or maintain conversation history. Local fallback QA
is explicitly unsupported. The UI can show multiple interactions, but each API call is independent.

## Computer A: small checkpoints in order

### 1. Validate a real comparison flag

Use a fixed side-view recording with two similar-paced comfortable reps, followed by a
noticeably slower third rep. Include a brief straight-arm pause before and after the set.
Record the human count and identify which rep changed pace. Keep the original file private.

Run the existing extraction/replay tools in apps/api/VIDEO_SETUP.md and examples/README.md.
The replay tool now supports `--expected-duration-change-reps 3` and a separate excursion
expectation; omitted rules are unchecked, and options without numbers assert zero flags.
It catches missing/extra flags while preserving input poses and timestamps. The four saved
recordings pass zero-flag regressions; this preparation does not complete the positive check.
Review every counted interval against the video, then check that the third rep's timing
comparison, reference values and flag agree with the footage. Review the coach's evidence
and the UI seek after B's integration. Keep thresholds fixed during this check; a failed
case is evidence to investigate, not a reason to force a flag.

Done when: a reviewed positive case and the existing unflagged clips are documented, or
the failure and next fix are recorded honestly. A timing flag does not validate the separate
excursion-reduction rule. That still needs its own real example before demonstrating it.

### 2. Improve measurement availability and tracking feedback

**Completed:** see [TRACKING_FEEDBACK.md](../apps/api/TRACKING_FEEDBACK.md). Existing
camera-quality text now reports angle/landmark sample coverage and blocked joints. No
schema change; 311 tests pass and the four saved real-pose replays retain 3/1/1/2 reps.
The next independent implementation is checkpoint 3; checkpoint 1 still needs new footage.

Expose useful measured coverage/reasons for missing joints instead of only generic limitations.
Start with the selected shoulder/elbow/wrist; evaluate hip/ankle coverage before body-line work.
Do not label landmark visibility as camera-angle correctness or invent a quality percentage.
Prefer existing contract fields; coordinate any new structured field before B relies on it.

Tests: missing/unknown visibility, offscreen points, one visible side, tracking gaps, recovery,
and unchanged completed-rep counts. Recheck all four saved real pose captures. This work can
proceed while waiting for a new recording or B's frontend PR.

### 3. Add one useful form-related measurement, then review its interpretation

**Measurement completed:** [BODY_LINE.md](../apps/api/BODY_LINE.md) defines the per-rep
median shoulder–hip–ankle angle. Synthetic tests, saved-clip regressions, independent
arithmetic and seven actual-frame overlays were checked. No form cue/score is implemented.
The next decision is validation of interpretation, alongside the pending real comparison clip.

**Coaching follow-up completed:** the coach can describe these medians with concrete evidence
paths, rejecting inconsistent sample/side metadata. Local next-set feedback can include it;
the optional selector can choose it for QA. This is an explanation of geometry, not a
validated corrective cue. Real positive comparison validation still needs a new recording.

Candidate: side-view shoulder–hip–ankle alignment during a rep, only when those landmarks
are reliably observed. First document geometry, units, measurement window, missing-data policy
and camera limitations. Then test synthetic geometry and inspect matching real frames.

Only after that evidence exists, decide whether a conservative alignment-change review cue
is supported. No universal good/bad threshold, injury claim, or confident conclusion from an
occluded joint. This is a separate feature commit, not a side effect of the tracking work.

### 4. Decide scoring explicitly

Scores remain part of the original product vision and are unfinished. Follow SCORING.md:
define observable inputs, a documented versioned rubric, weights and unavailable cases;
compare results with reviewed footage before displaying a score. A side view does not make
every symmetry/stability/ROM metric measurable. Do not fill all five fields merely to complete
a dashboard. If evidence/time is insufficient, demo measurements and changes with null scores.

### 5. Review B's completed integration

Test actual upload → skeleton → rep results/comparisons → coach, and live start → count →
finish → reset. Check stale responses, lost tracking, no person, backend unavailable, missing
model and local coach fallback. Browser Lite and upload Full pose models can produce different
landmarks: test both paths, even though they share the Python analyzer.

Run backend tests/schema checks and frontend tests/lint/types/build on the integrated commit.
Use the actual presentation laptop for a physical-camera rehearsal. Fix specific failures
before starting the visual overhaul. B's own demo check is useful but does not replace this
integration review on Computer A.

## Then: visual overhaul on Computer A

After B's PR is integrated and ownership transferred, agree the visual direction and redesign
landing, upload, camera and results as one coherent experience. Preserve file/pose pairing,
timestamps, raw pose input, request lifecycle, unknowns and evidence. Retest behavior after
each screen; polish keyboard/mobile states as well as appearance.

Finish with two rehearsals, a known-good private backup clip, screenshots/demo recording,
the README/pitch and Devpost submission. Freeze working dependencies before presenting.

## Deliberately later

Lunges and other gym analyzers, automatic exercise recognition, ghost motion, barbell path,
custom ML training, history/accounts, voice feedback and fatigue claims. Add one only if
the recorded push-up demo and integration are already reliable and time remains.

## Validation baseline

Latest backend rehearsal: fresh extraction through multipart route handling, returned pose
track → identical analysis, and local next-set coaching pass for all four original clips.
Counts remain 3/1/1/2; blank input returns unknown count and corrupt MOV returns 400 followed
by successful uploads. See apps/api/VALIDATION.md for timings and test scope. Current code
checkpoint has 375 passing tests. The human confirms new gym footage and B's PR are still
in progress; do not treat this rehearsal as completion of those pending checkpoints.

Coach follow-up: 359 backend tests plus lint/format/schema checks passed. Four saved analyses
passed local next-set coaching checks with body-line evidence; no paid API calls.

Body-line checkpoint: **335 backend tests passed** on 2026-09-26. One existing Starlette TestClient
deprecation warning remains. 35 frontend tests plus lint, types,
contracts and production build passed again; rerun those on B's new commits rather than treating
this earlier result as coverage of work still in progress.

For each checkpoint: implement → focused tests → saved-clip regression where relevant →
review diff → small commit → push. Tests use local/fake coach providers and do not spend API
credits. Native CV and deliberate live OpenAI checks are separate from the unit suite.
