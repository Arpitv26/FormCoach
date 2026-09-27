# Gym upload development — September 27, 2026

Demo direction: live push-ups, plus one uploaded clip each for incline dumbbell bench press,
cable lateral raise and lat pulldown. Triceps is out of scope. Computer A owns both apps.
No training or new dependencies. Filenames are human annotations, not classifier labels.

## Current checkpoint: original uploads and visual coaching

The human's browser screenshots exposed failures on the **original 4K files**, not the
previously selected 1080p exports. These results supersede the historical milestone counts
and strict missing-sample behavior below. Different exports can produce different poses.

Counting changes are gym-specific:

- Incline press v2 retains bent <=100°, rising >=110°, 100 ms raw dwell and three-sample
  median; extension tolerance is now >=145°. A 1,200 ms minimum interval between completion
  timestamps rejects rapid duplicate angle cycles. It can miss genuinely faster cycles.
- Press and pulldown may preserve an unfinished phase across at most 200 ms since the last
  usable angle. Missing data clears the median and dwell clocks; fresh observed samples must
  confirm completion. There is no interpolation. Longer loss resets the unfinished phase.
- Gym upload/CLI extraction can choose the clearly dominant person when visible landmark
  bounding area is at least twice the second person's. Comparable people remain unknown.
  This heuristic is not identity tracking: review the skeleton. Push-up extraction and
  push-up/squat/cable segmentation policies are unchanged.

`inclinedDumbellChestPressGoodFormSideView2.MOV` reproduced **3** under the prior rules,
then **7** with the correction. The human reports 7 including the initial lift, 6 excluding
it. Seven start/completion frame pairs were reviewed; the first interval includes sitting
back into the bench/setup. It must not be treated as seven independently verified working
reps or used as an ideal timing/range baseline. Completion times on the original saved poses:
2.335, 6.468, 8.737, 11.205, 14.205, 17.673, 21.208 seconds.

`latPulldownGoodFormSideView.MOV` reproduced **5**, then **6** with foreground selection.
Six recovered overlays at 18.142–18.475 s track the main seated exerciser, not a bystander.
`latPulldownBadFormSideView.MOV` reproduced **3**, now **5/6** in a fresh upload. The second
pull has only two raw <=70° observations, at 5.068 and 5.135 s, insufficient for the 100 ms
pull dwell. The missing count remains a documented limitation, not a bad-form label.

Saved 1080p pose replay now counts annotated bad-form press left **7/7**, right **6/6**,
angled **4/4**; bad pulldown **4/6**. Selected exports retain lat **6**, incline angled2 **7**,
lateral side **7**. Back-view lateral raises still count **0**. These are development
regressions, not independent validation or proof all detected intervals match human reps.

Optional visual review uses GPT-5.4 sampled images independently of completed-rep counting.
The original bad pulldown's actual HTTP review identifies repeated backward/forward torso
rocking and suggests a steadier lean, with playback references. It does not replace the
5/6 count. Press/normal-pulldown visual reviews also completed, and actual chat requests
returned a seven-rep timestamp/angle breakdown and specific torso-rocking guidance.
See ../../docs/AI_COACH.md for sampling, settings and interpretation limits.
Final fresh HTTP checks with both extraction and visual review enabled retain original
incline side2 **7**, changed pulldown **5/6**, and selected lateral side export **7**; all three
return completed GPT-5.4 visual reviews. The normal pulldown foreground-selection upload
retains **6**, with its recovered frames checked against the main exerciser.

Checks: **550 backend / 55 frontend tests**, lint/format, schemas/types and production build.
Eight saved push-up/blank captures preserve complete geometric results against e6693fd:
counts **3/1/1/2/4/19/0/unknown**, rep timings/angles, flags, tracking and movement observations.
6942 retains the rep-3 timing flag; badpushups retains five independent bend intervals.
Browser automation remains unavailable (`codex app-server` missing). Native HTTP upload and
real OpenAI chat were checked; final browser rendering/seek rehearsal remains manual.

## Earlier implementation milestones (historical)

## First supported exercise: lat pulldown

Wire ID `lat-pulldown`, shared by selection, upload, analysis and coaching. The existing
v1.0 string IDs and numeric measurement dictionary support this without a schema change.
The upload page accepts an exercise query and remounts its upload session when it changes,
so old clips/results/requests cannot become a different exercise's evidence. Push-up live
capture is unchanged. Incline press and lateral raise are also implemented below.

Rules: side-view shoulder–elbow–wrist angle; visibility >=0.7, in-frame, nondegenerate joints.
Lock the first usable side, left on a tie. Require a return angle >=120°, a pull <=70°, then
return >=120°. Transitions have 10° hysteresis, 100 ms consecutive raw dwell plus a causal
three-sample median. Counted duration 800–15000 ms. Missing angle or gaps >300 ms discard
unfinished cycles. These engineering zones are not full-extension/depth/form targets.

Each cycle reports existing elbow min/max/excursion, duration, time to/from minimum and
matching playback timestamps. Scores/confidence remain null. No torso-swing, equipment,
bilateral-symmetry or good/bad-form detector; no automatic rep-change flags for this exercise.
Coach evidence includes selected exercise, requested rep timing and elbow range.

## Private recordings reviewed

14 gym originals are in the repository root and ignored. `NEW_SESSION_PROMPT.md` was not
present; the session used the handoff pasted by the human. Original filenames describe
exercise/view and intended good/bad form, but do not supply exact counts or fault descriptions.
The human subsequently supplied the bad-form counts and intended changes recorded below.

Private 1080p exports and poses: `apps/api/artifacts/gym-review/`. Originals are preserved.
The two good-form lateral-raise originals exceed the 250 MiB upload limit (264.4 / 290.6 MiB).
Exports fit the existing limit; no upload-limit relaxation or silent file substitution.
Analyze and play back the same named export. Resizing can change pose estimates.

`latPulldownGoodFormSideView-1080p.mov`: 331/331 usable right-elbow samples; six observed
cycles. Pulled/return frame pairs were visually reviewed at:

| Cycle | Start | Minimum angle | Return |
| --- | --- | --- | --- |
| 1 | 1.067 s | 1.867 s | 3.602 s |
| 2 | 4.268 s | 5.202 s | 7.137 s |
| 3 | 7.870 s | 8.670 s | 10.738 s |
| 4 | 11.338 s | 12.205 s | 14.207 s |
| 5 | 14.807 s | 15.607 s | 17.607 s |
| 6 | 18.142 s | 19.075 s | 21.008 s |

This is development-footage review, not an independent accuracy benchmark. The original
4K extraction has six no-pose/multiple-person samples; do not assert it produces the same
results. The bad-form export has tracking interruptions and requires separate interpretation;
its filename does not authorize inventing a detected defect.

Initial signal review: several incline clips begin in the bent-arm position, so their cycle
orientation must differ from push-ups. Lateral-raise back views have substantial occlusion/
tracking interruptions, while side-view shoulder angles suffer projection ambiguity. Do not
lower visibility thresholds or bridge missing landmarks simply to obtain the expected count.

## Reproduce

From `apps/api`:

```bash
.venv/bin/python -m app.tools.analyze_video \
  artifacts/gym-review/latPulldownGoodFormSideView-1080p.mov \
  --exercise lat-pulldown --output artifacts/lat-repeat-1
```

Choose a new output folder each run. The default remains push-up for existing commands.
Open `http://localhost:3000/upload?exercise=lat-pulldown` and choose the same export.

## Checks

Baseline: 447 backend / 53 frontend tests. Added lat mechanics tests cover both sides,
missing/unknown/offscreen landmarks, gaps, side lock, holds, spikes, partial cycles, cumulative
replay, matching live/upload reps, multipart pose pairing, local coach and CLI exercise ID.
Both schema/type checks, lint, formatting, TypeScript and production build pass.
Browser automation was unavailable in this session (the computer-use service could not start);
actual browser upload, playback seeks and exercise switching still require a manual check.

Human counts supplied during review (all filenames labeled BadForm): cable lateral raise
back view **6**, side view **7**; lat pulldown side view **6**; incline press left side **7**,
right side **6**, angled view **4**. Intended fault descriptions are recorded below.
These supersede the earlier missing-count note. The current bad-form lat-pulldown export
counts **3/6** with 8 tracking breaks: a recorded failure, not six verified detections.

First milestone native check: real multipart upload of the good lat-pulldown export returns
`complete`, 6 reps, 331 poses. Rep objects exactly match the reviewed saved-pose analysis.
Eight saved push-up/blank captures retain counts 3/1/1/2/4/19/0/unknown; the 6942 rep-3 flag
and badpushups' five independent observations remain intact.

First checkpoint: **463 backend tests / 53 frontend tests pass**. One real OpenAI request
correctly answered the third lat-pulldown rep duration as 2.87 seconds (7.87–10.74 s) with
matching evidence paths. This verifies one answer, not general coaching accuracy.

## Second milestone: incline dumbbell bench press

Wire ID `incline-dumbbell-bench-press` now supports the same selection/upload/results/coach
path. New `segment_incline_presses` observes bent arms <=100°, then a press through >=110°
to >=150° extension; 100 ms raw dwell plus median confirmation. Extension completes a rep;
returning to bent arms rearms it. A static overhead hold or lowering alone cannot add reps.
Missing landmarks and >300 ms gaps reset an unfinished press. Intervals last 300–15000 ms.

Timing starts on the first sample of the confirmed bent-arm run, not at exact anatomical
lifting onset. Min/max/excursion begin at bent-position confirmation and end at confirmed
extension. Bottom pauses are included; lowering before the bent zone is excluded. Do not
compare these interval durations with full push-up or lat-pulldown cycles. Thresholds are
engineering heuristics, not depth or lockout targets. No weight/bench-angle/form assessment.

Selected export `inclinedDumbellChestPressGoodFormAngledView2-1080p.mov`: 300/300 usable
selected-left-elbow samples, **7 presses**. Seven bent/extended video pairs were reviewed;
confirmed extension times are 1.133, 3.868, 6.337, 9.003, 12.138, 14.740 and 18.008 s.
Fresh native multipart upload returns the same seven intervals and 300 playback poses.
This is a development check; a human good-form count was not supplied. Another right-side
good-form export yields seven, but its full correspondence has not yet been independently reviewed.

Known annotated failures on BadForm exports: angled **3/4**, left side **5/7**, right side
**3/6**. Preserve these failures. A different count is not a bad-form detection. Interrupted
tracking and insufficient sustained zone evidence require clip-specific review; do not
force counts or claim that every human rep met this narrower counter definition.

Checks: **485 backend tests**, including multi-rate/cumulative press sequences, both sides,
missing/unknown/low/offscreen landmarks, gaps, no rearming, spikes, long holds, expired and
unfinished presses, coach naming and extension completion. Existing push-up/lat tests pass.
Frontend lint/types pass; browser verification remains blocked by unavailable computer use.

Human descriptions of intended changes: press — elbows farther out, dumbbells not brought
together at the top, possibly legs lifted at the end of one clip; pulldown — larger backward/
forward torso swing and overhead stretch; lateral raise — cross-body swing from low near
the opposite knee to above shoulder/head level, with torso turning/movement. These are
annotations for comparison, not implemented detections. The pose model does not track
dumbbells, and a single view cannot establish elbow tuck or axial rotation reliably.

## Third milestone: cable lateral raise

Wire ID `cable-lateral-raise` is connected through selection, upload, results and coach.
Uses the selected side's projected hip–shoulder–elbow angle: confirmed low <=30°, rising
>=40°, completion >=60°, with the same causal median/raw 100 ms dwell and missing-data
resets as incline press. A shared rising-angle segmenter preserves incline behavior.
These are projection-dependent counting zones, not anatomical shoulder abduction targets.
Counted intervals cover the confirmed low run through the raised zone, including pauses;
lowering rearms the next rise. Scores and automatic form/change flags remain unavailable.

Selected export `cableLateralRaisesGoodFormSideView-1080p.mov`: **7 raises**, 343 playback
poses; native multipart upload exactly matches saved-pose rep objects. Status is `partial`
because 8 samples are unavailable with 6 tracking breaks, mostly after completed raises.
Both this clip and the BadForm side view have seven separate low/raised frame pairs reviewed.
The BadForm side view counts **7/7**. Both back views count **0** with substantial tracking/
projection problems; the bad back view's human count is **6**. Do not use those for the demo.
Matching the bad side-view count does not mean the intended faults were classified.

Shoulder min/max/excursion and time-to/from-minimum keys use the existing numeric dictionary.
Results and coaching render these with shoulder labels; elbow-only push-up behavior remains.
Checks: **502 backend / 54 frontend tests**, lint, formatting, TypeScript, schema/type checks,
and production build pass. Browser upload/playback/switching still need manual verification.

## Fourth milestone: descriptive torso feedback

Lat pulldown and lateral raise now add raw 2D shoulder-to-hip tilt relative to upward image
vertical to each counted rep: minimum, maximum, range and sample counts. The first maximum
has a playback marker. Results and both local/OpenAI coach evidence can describe the range.
The whole counted interval must have usable selected-side shoulder/hip landmarks, at least
three samples, both endpoints and no gap >300 ms. Otherwise angles are null. These measurements
never alter counts. There is no smoothing, interpolation, swing threshold or form classification.
Unsigned range is not total angular travel and cannot establish direction/rotation/momentum.

Development comparison on the side-view exports:

| Clip annotation | Counted intervals | Torso angle range within each interval |
| --- | --- | --- |
| Lateral raise GoodForm | 7 | 13.0°, 2.8°, 4.0°, 7.4°, 6.0°, 6.5°, 3.2° |
| Lateral raise BadForm | 7 / human 7 | 23.0°, 31.7°, 36.8°, 45.1°, 42.5°, 38.3°, 33.8° |
| Lat pulldown GoodForm | 6 | 5.9°, 5.8°, 8.4°, 7.5°, 6.8°, 6.5° |
| Lat pulldown BadForm | 3 / human 6 | 11.0°, 20.4°, 16.6° |

Numbers apply only to detected intervals, not matching human rep ordinals when counts differ.
Raw extrema can be sensitive to pose noise. Eight minimum/maximum video overlays reviewed:
rep 4 of each lateral side-view clip and detected rep 1 of each lat clip. Visible shoulder/hip
lines support the descriptive geometry; no independently calibrated ground-truth angles exist.
Do not use these two same-session recordings to establish a universal good/bad threshold.

Final checks: **523 backend / 54 frontend tests**; lint, formatting, types, schema/type checks
and production build pass. Eight saved push-up/blank captures preserve summary, reps,
measurements, timeline, issues, camera feedback, status and movement observations relative
to `e6693fd` (counts 3/1/1/2/4/19/0/unknown). IMG_6938 already has one body-line observation;
badpushups retains five. Existing three gym demo rep objects remain unchanged apart from
new torso fields/markers. New tests cover known angles, portrait/landscape/mirroring,
missing/low/unknown/out-of-frame/degenerate points, interval gaps/boundaries, cumulative
stability and inconsistent coach metadata.

Fresh native BadForm lateral side-view upload after torso additions returns complete, 7 reps.
Detected rep 4 has 1.680°–46.743° torso tilt (45.063° range), peak marker 7.482 s. A real
OpenAI question about that rep returned approximately 45°, 1.7°–46.7°, and the correct
6.75–8.40 s interval with matching evidence paths. This verifies one answer, not general
form-advice accuracy; the model's optional offer of stabilization tips is not a finding.

## Rehearsal files and remaining manual checks

Start both apps using README commands, then open `http://localhost:3000/upload` and select
the exercise. In the file picker use Command+Shift+G and paste:

```text
/Users/arpit/Developer/helloHacks/helloHacks/apps/api/artifacts/gym-review
```

| Exercise | Private export | Expected development result |
| --- | --- | --- |
| Lat pulldown | `latPulldownGoodFormSideView-1080p.mov` | 6, complete |
| Incline dumbbell bench press | `inclinedDumbellChestPressGoodFormAngledView2-1080p.mov` | 7, complete |
| Cable lateral raise | `cableLateralRaisesGoodFormSideView-1080p.mov` | 7, partial tracking |

Verify skeleton alignment, seek a rep/torso marker, ask the coach about that rep, then switch
exercises and check that the old clip/results disappear. Do a fresh physical live push-up set.
The computer-use service failed to start in this session, so these browser/manual checks
are explicitly pending. Native uploads of all three selected exports passed before torso
additions; pose replay and HTTP coverage exercise the same analyzer. The significant UI
redesign is deferred; current changes only make exercise selection/results work.
