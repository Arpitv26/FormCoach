# Push-up measurements — timing and observed elbow excursion

This checkpoint adds descriptive numbers to each completed push-up's existing
`measurements` dictionary. Live batches, local video analysis, and HTTP uploads all use
`RuleBasedAnalyzer`, so they expose the same fields. Contract version stays **1.0**;
no schema or generated TypeScript changes are needed for extensible measurement keys.

## What the numbers mean

`Left` below becomes `Right` when the existing visibility policy locks to the right elbow.
All angles use the shoulder-elbow-wrist triplet, corrected for image aspect ratio, then
smoothed using the counter's causal median of three usable frames. The selected side
never changes during a set.

| Key | Definition | Suggested UI label |
| --- | --- | --- |
| `durationMs` | `endMs - startMs` (existing field) | Counted rep time |
| `minSmoothedLeftElbowAngleDeg` | Lowest smoothed angle after descent confirmation through completion (existing field) | Minimum elbow angle (2D) |
| `maxSmoothedLeftElbowAngleDeg` | Highest smoothed angle over that same window | Maximum elbow angle (2D) |
| `smoothedLeftElbowExcursionDeg` | Maximum minus minimum over that same window | Observed elbow range (2D) |
| `angleMeasurementStartMs` | Clip/set timestamp when descent was confirmed, inclusive | Developer evidence: angle window start |
| `timeToMinElbowAngleMs` | First minimum-angle timestamp minus `startMs` | Time to minimum angle |
| `timeFromMinElbowAngleMs` | `endMs` minus that minimum-angle timestamp | Time after minimum angle |

The two time parts sum exactly to `durationMs`. The minimum timestamp already exists in
`keyMoments` as `minimum_elbow_angle`; no duplicate event type was added. An exact plateau
uses its first minimum sample; tiny model fluctuations can move the measured minimum.

Rep start is the first observation of subsequently confirmed descent. Angle extrema begin
at the later confirmation time to preserve the existing minimum-angle definition. The
window includes the completion observation and excludes later top pauses or other reps.
It does not include the entire initial straight-arm pose. Its excursion is an observed
range over this window, not a calibrated anatomical/full-exercise range of motion.

## Interpretation limits

- Timing includes smoothing, phase-confirmation delay, and pauses. These are not isolated
  eccentric/concentric or lowering/lifting durations. A long bottom pause contributes to
  time after the first minimum. A later lower angle can shift that split.
- Angle values depend on the camera view and pose estimates. Compare descriptive values
  cautiously within a fixed-view set; do not rank clips filmed from different angles.
- Greater excursion or faster/slower movement is not automatically better form. There
  are no ideal tempo targets or quality scores. The subsequent [comparison checkpoint](COMPARISONS.md)
  adds evidence-backed review flags for differences, not good/bad form classifications.
- Scores in `metrics` remain null, including `rangeOfMotion` and `tempo`. Never put degrees
  or milliseconds into those 0–100 score fields. No known worst rep exists yet.
- Missing/low-confidence landmarks and gaps still discard unfinished reps. Those attempts
  receive no invented measurements. Completed reps retain their original values.

## Synthetic example for Computer B

`contracts/examples/pushup-analysis.json` is a new one-rep **SYNTHETIC DEMO DATA** fixture
computed under the original policy from `apps/api/examples/synthetic-pushup-capture.json`.
Counter v2 replays that capture with a 500–2100 ms counted interval and 600–2100 ms angle
window; the fixture preserves its authored original interval. See COUNTING.md.
It is authored geometry,
not a person's video. The old squat fixture remains available for compatibility.

The example has an angle window of 800–2300 ms, minimum 90°, maximum 170°, observed range
80°, counted duration 1700 ms, time to minimum 500 ms, and time after minimum 1200 ms.
Its minimum occurs at 1100 ms. Scores stay null and provenance is explicitly synthetic.
There is no matching video: do not seek into a real clip using this fixture's timestamps.

B can integrate later. Read `docs/FRONTEND_HANDOFF.md` and `HTTP_UPLOAD.md` when ready.
Display durations in seconds (`ms / 1000`) and round angle display to about one decimal;
extra machine precision is not a statement of measurement accuracy. Older results may
lack these new dictionary keys: show “Not available” instead of zero.

## Evidence and repeat checks

Run from the repository root:

```bash
apps/api/.venv/bin/python -m pytest -q apps/api/tests/test_pushup_measurements.py apps/api/tests/test_pushup_analysis.py
```

Tests use known geometry/signals to check both sides, extrema, spike rejection, per-rep
isolation, bottom pauses, source timestamps, loss/recovery, schema compatibility, and the
synthetic example. Existing live replay tests verify that completed measurements do not
change when more frames are appended. Existing squat wire measurements are unchanged.

All four recorded pose captures were replayed through HTTP route handling with TestClient.
Counts remain 3/1/1/2; all seven rep boundaries and minimum moments match the prior real-upload
results. Independent median-window calculations reproduce the new extrema and excursions.
This check reuses saved real poses: no new extraction or human annotation of joint angles.
It verifies computation/integration, not camera measurement accuracy.

Local outputs are ignored under `artifacts/measurement-check/`. See VALIDATION.md for the
recorded results. To rerun on video from scratch, use the existing VIDEO_SETUP.md command
with a new output directory; `analysis.json` now contains these measurements automatically.
