# Remaining work — after backend and overlay integration

## Current direction — September 27, 2026

The demo is **live push-ups plus uploaded incline dumbbell bench press, cable lateral raise
and lat pulldown**; triceps is removed. A owns both apps. Fourteen private gym clips are now
available. All three upload checkpoints are implemented. The selected 1080p exports count
6 pulldowns, 7 presses and 7 lateral raises; several bad-form/back-view clips still undercount.
See [gym exercise evidence](../apps/api/GYM_EXERCISES.md). Descriptive torso measurements are
implemented for lat pulldown/lateral raise. Browser rehearsal and a fresh physical push-up
set precede the deferred visual overhaul. Investigate failed views from actual poses without
equating missing counts with bad form; do not promise equipment/rotation detection.
The earlier plan below is historical where it conflicts with this direction.


Updated 2026-09-26. Main `7f44566` includes PRs #1–#5. The next checkpoint fixes a failed
physical rehearsal and the confusing coach/results flow. Read LIVE_REHEARSAL_FIX.md first.

## Current priority: useful feedback when no complete reps count

**First observation implemented:** see apps/api/MOVEMENT_OBSERVATIONS.md. A separate geometry
pass now supplies timestamped body-line bends to results and coach even with zero reps.
badpushups has five intervals; these are not five classified attempts. Existing clip counts
are unchanged. The remaining work below is broader interpretation/independent validation,
not a claim that this narrow observation fully assesses form.

The latest human rehearsal reports that the long upload now works and live counted 19;
a brief pause at the top helps live counting. This is human feedback, not a new captured
live accuracy benchmark. Keep the existing counting policy while investigating new evidence.

`badpushups.MOV` demonstrates the next product gap: the human deliberately moved the torso/
hips for about 4–5 attempts. Fresh extraction returns zero completed cycles despite 187/188
usable selected-elbow samples. Only one raw sample reaches the current bend zone; a sustained
bend is required. This result is not a bad-form classification. Read
[BAD_MOVEMENT_REVIEW.md](../apps/api/BAD_MOVEMENT_REVIEW.md) for the measured evidence.

Next implementation checkpoint:

1. Analyze reliably visible movement intervals independently of completed rep segmentation.
   Keep attempted movement separate from the completed-rep count; do not force this clip to
   count 4 or 5 or infer that every uncounted movement is an incorrect push-up.
2. Start with one descriptive elbow/body-line observation and timestamps. Review matching
   normal and deliberately changed footage before assigning any specific form label.
   The present unsigned body-line angle cannot distinguish hip sag from pike.
3. Expose that evidence in results and conversational coaching, including zero-count results.
   Any additive contract requires matching documentation, examples, types and tests.
4. Test normal recordings, static holds, partial movements, fast turns and tracking gaps;
   preserve the working counts. Use a separate clip for validation after tuning.
5. Then continue the visual overhaul: show a short useful explanation and one next action;
   keep diagnostic detail expandable. Do not present developer troubleshooting as coaching.

Conversation fix completed in this checkpoint: requested rep numbers and follow-up context
now take priority over generic six-rep highlights. A real OpenAI request correctly answered
rep 12's duration; 428 backend tests pass. Specific form findings remain unimplemented.
More labeled videos help us develop and test the analysis rules; adding files does not train
MediaPipe or OpenAI. No model training is planned for this checkpoint.

## Earlier counting checkpoint

**Latest counting correction:** read [COUNTING.md](../apps/api/COUNTING.md). The new live
capture reproduced 4 and now returns 5; IMG_6943 reproduced 5 and now returns 19 distinct
cycles. The human reported 20; a twentieth cycle is not established by the video review.
Old top/bottom dwell and return thresholds merged continuous cycles. Counter v2 addresses
that behavior; original five recordings retain 3/1/1/2/4. A fresh physical live set and
independent footage remain required before declaring counting reliable.
This is the current work order. Keep the longer product vision in PRODUCT_SCOPE.md;
do not try to finish every stretch feature before the demo.

## Ownership confirmed by the humans

- **Computer B:** feature handoff complete in merged PR #4. Coordinate any further screen edits.
- **Computer A:** owns integration, backend and the upcoming frontend visual overhaul.
  Preserve tested upload/pose pairing, raw live input, request lifecycle and evidence behavior.
- **Next order:** implement the bounded movement-feedback checkpoint above, preserve counting
  regressions, capture any new live mismatch, then continue the visual overhaul in small commits.

## What the code actually does today

| Capability | State | Evidence / remaining limitation |
| --- | --- | --- |
| Upload decoding and pretrained pose extraction | Implemented | Five real MOV clips; portrait rotation supported; bounded inputs and cleanup |
| Push-up counting | Implemented | Human counts 3/1/1/2/4 match; small sample, not a general accuracy benchmark |
| Rep timestamps and elbow measurements | Implemented | Duration, min/max, excursion, time around minimum angle; 2D observations |
| Rep comparisons | Timing policy v2 implemented | Change must exceed a margin against both preceding durations; 6942 rep 3 now flags as a development regression. Separate validation still needed |
| Tracking coverage / missing-joint feedback | Implemented | Sample counts and actionable joint reasons; no readiness or quality score |
| Live analysis API | Implemented | Physical rehearsal failed 5 → 2; false missing-pose emission fixed, new capture/replay needed |
| Live / uploaded skeleton | Implemented | Browser and portrait/landscape playback checks; actual webcam smoothness needs recheck |
| Coach API | Implemented | Integrated panel; actual local summary/next-set/evidence links verified; optional OpenAI configured separately |
| Form score and five quality metric scores | **Missing** | `analysis/scoring.py` is a placeholder; real scores remain null |
| Body-line geometry | Implemented | Median 2D shoulder–hip–ankle angle per rep; seven real-frame checks; not a form assessment |
| Body alignment / depth-quality coaching | **Missing** | A reliable interpretation and corrective cue still need separate validation |
| Full-body visibility / camera orientation | **Missing** | Required-joint visibility is checked, but these session-level judgments stay unknown |
| Worst-form rep ranking | **Missing** | No quality score exists; a flagged change can be reviewed without calling it the worst rep |
| Other gym exercises / automatic recognition | **Missing** | Registered profiles and UI choices do not establish analysis support |

The current coach UI requests short generated replies grounded in numeric evidence and sends
the last six exchanges for follow-ups. The server remains stateless and never watches video.
Recognized missed-count questions use local troubleshooting guidance. Legacy evidence selection
remains available. Read AI_COACH.md for limits and the distinction between the two modes.

## Computer A: small checkpoints in order

### 1. Validate a real comparison flag

**Original failure:** IMG_6942 was supplied and reviewed: four counted reps with durations
1.735 / 1.400 / 3.068 / 1.068 s. Video review agrees with the slow-third/fast-fourth annotation.
The expected timing flag was missing because the first two durations have 21.37% spread,
just above the former 20% reference gate. Replay correctly reported `comparison_mismatch`.
See [REVIEW_6942.md](../apps/api/REVIEW_6942.md) for that original unchanged-policy check.

**Implemented follow-up:** timing policy v2 requires the current duration to differ from BOTH
previous durations in the same direction by the existing max(500 ms, 30% of each reference)
margin. It supplies versioned numeric boundaries and reasons for unavailable comparisons.
All five saved captures pass count/stability checks; 6942 now flags rep 3 and the local coach
explains it. Rep 4 does not differ enough from BOTH references to flag. The first four clips
remain unflagged and all rep measurements/timestamps are unchanged. This is a development
regression, since 6942 motivated the revision. B's integrated UI now passes the actual-video
flag/coach/seek check. Next: validate v2 on separate footage. Do not keep retuning against 6942 or claim general detection accuracy.

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
Checkpoint 3 measurement work is also completed; independent timing-policy validation remains open.

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
The next decision is validation of interpretation, alongside independent timing-policy validation.

**Coaching follow-up completed:** the coach can describe these medians with concrete evidence
paths, rejecting inconsistent sample/side metadata. Local next-set feedback can include it;
the optional selector can choose it for QA. This is an explanation of geometry, not a
validated corrective cue. Timing v2 flags the development clip; separate validation is still needed.

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

**Completed code/integration review:** PR #4 merged; 399 backend and 49 frontend tests plus
lint/types/contracts/build pass. Real IMG_6942 upload, timing flag, coach and seeks pass.
Simulated browser camera → actual API final/reset/stop passes. Physical rehearsal below remains open.

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

Current integrated review: 399 backend / 49 frontend tests, contracts, lint, types, build and
PR #4 CI pass. See INTEGRATION_STATUS.md for actual-browser scope and remaining human checks.

### Earlier backend checkpoints

Timing v2: 399 backend tests and 35 frontend tests pass; five saved-pose replays keep all
counting/geometry/timestamps unchanged, with the intended rep-3 duration flag on 6942 only.
Local coaching evidence checks pass; no paid request. Frontend lint/types/contracts pass.

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
