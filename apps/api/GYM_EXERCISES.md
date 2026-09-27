# Gym upload development — September 27, 2026

Demo direction: live push-ups, plus one uploaded clip each for incline dumbbell bench press,
cable lateral raise and lat pulldown. Triceps is out of scope. Computer A owns both apps.
No training or new dependencies. Filenames are human annotations, not classifier labels.

## First supported exercise: lat pulldown

Wire ID `lat-pulldown`, shared by selection, upload, analysis and coaching. The existing
v1.0 string IDs and numeric measurement dictionary support this without a schema change.
The upload page accepts an exercise query and remounts its upload session when it changes,
so old clips/results/requests cannot become a different exercise's evidence. Push-up live
capture is unchanged. Incline press and lateral raise remain planned until their checkpoints.

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
An asynchronous clarification was requested; those human annotations remain unconfirmed.

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
right side **6**, angled view **4**. Specific intended fault descriptions were not supplied.
These supersede the earlier missing-count note. The current bad-form lat-pulldown export
counts **3/6** with 8 tracking breaks: a recorded failure, not six verified detections.

First milestone native check: real multipart upload of the good lat-pulldown export returns
`complete`, 6 reps, 331 poses. Rep objects exactly match the reviewed saved-pose analysis.
Eight saved push-up/blank captures retain counts 3/1/1/2/4/19/0/unknown; the 6942 rep-3 flag
and badpushups' five independent observations remain intact.

First checkpoint: **463 backend tests / 53 frontend tests pass**. One real OpenAI request
correctly answered the third lat-pulldown rep duration as 2.87 seconds (7.87–10.74 s) with
matching evidence paths. This verifies one answer, not general coaching accuracy.
