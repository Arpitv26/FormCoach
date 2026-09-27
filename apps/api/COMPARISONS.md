# Push-up comparisons — measured differences for review

This checkpoint compares each completed push-up with the **two completed reps immediately
before it**, within the same set and on the same locked anatomical side. It never changes
a past rep when future frames arrive. Rep 1 and rep 2 cannot have comparisons yet.

These are descriptive review flags. A longer rep or smaller observed angle range does not
by itself establish bad form, fatigue, inadequate depth, injury risk, or a need to move
faster/deeper. Scores, worst-rep ranking, and biomechanical assessment remain unavailable.

## Eligibility and rules

First require continuously usable elbow angles from the first reference rep's start through
the current rep's end, including time between reps. Any missing/low-visibility/invalid angle
or timestamp gap over 300 ms suppresses both comparisons for that rep. Later tracking loss
does not erase earlier results. After a gap, two new reference reps plus a current rep are
needed. An unfinished rep never receives a flag.

Reference values must be present and positive. Deltas use the median of the two preceding
values (their average for two numbers), not all reps or future data. Timing policy v2 requires
a substantial change from BOTH preceding durations in the same direction. Range retains
its separate reference-stability check.

| Metric | Reference stability | Flag threshold (inclusive) | Code |
| --- | --- | --- | --- |
| Counted duration (v2) | Both reference/current durations agree with their timestamps; continuous tracking | Longer than each reference by >= `max(500 ms, 30% of that reference)`, or shorter than each by that margin | `PUSHUP_REP_DURATION_CHANGED` |
| Observed elbow excursion | `max - min <= 10°` | Reduction >= `max(15°, 20% of median)` | `PUSHUP_ELBOW_EXCURSION_REDUCED` |

The absolute floors avoid highlighting tiny differences. Timing cannot flag a value between
the two previous durations, or a return to one previous duration. Both increases and decreases
can flag; an increase in excursion does not trigger the reduction rule. These are engineering
heuristics, not calibrated fitness thresholds. The existing 500 ms / 30% margins remain in
`PUSHUP_PROFILE.thresholds`; the former hard 20% duration-reference gate was removed after
the IMG_6942 failure. This is a policy change developed using that clip, not independent validation.

For references `a` and `b`, let `margin(t) = max(500, 0.30*t)`. The inclusive boundaries are:
`lower = min(a-margin(a), b-margin(b))`, `upper = max(a+margin(a), b+margin(b))`.
A timing flag requires `current <= lower` or `current >= upper`. A negative lower boundary
means no positive completed duration can trigger the shorter rule with those references.
These are review boundaries, not a recommended tempo. Timing still includes pauses and
segmentation delay; sampling uncertainty is not calibrated or represented as confidence.

Camera orientation/stability is not detected. Even continuous landmarks cannot prove the
camera view stayed fixed. Moving the camera, changing body orientation, or estimation errors
can change these values. Review matching video before interpreting a flag. See MEASUREMENTS.md
for the angle window and why counted time includes pauses and phase-confirmation delay.

## Existing v1.0 response

No domain fields or generated types change. New numeric evidence lives in the extensible
per-rep `measurements` dictionary:

| Key | Meaning |
| --- | --- |
| `comparisonReferenceStartRep`, `comparisonReferenceEndRep` | Inclusive reference rep numbers, e.g. 1 and 2 |
| `referenceMedianDurationMs` | Median reference counted duration |
| `durationDeltaMs`, `durationDeltaPercent` | Current minus reference; percent = `100 * delta / reference` |
| `durationChangeThresholdMs` | Effective distance from the reference median to the review boundary in the current delta's direction; with nonnegative delta use upper |
| `durationComparisonVersion` | `2` for the current timing policy; absence denotes older outputs |
| `referenceMinDurationMs`, `referenceMaxDurationMs` | Smaller/larger of the two prior counted durations |
| `durationReviewLowerBoundMs`, `durationReviewUpperBoundMs` | Inclusive current-duration boundaries for shorter/longer review flags, in milliseconds |
| `referenceMedianElbowExcursionDeg` | Median reference observed excursion on the locked side |
| `elbowExcursionDeltaDeg`, `elbowExcursionDeltaPercent` | Current minus reference; negative means less observed excursion |
| `elbowExcursionReductionThresholdDeg` | Threshold applied to the reduction |

Eligible comparisons expose numbers even when no threshold is crossed. Ineligible metric
keys are absent, not zero. No keys means fewer than two preceding completed reps,
insufficient continuous tracking, invalid durations or invalid/unstable range references.
Existing `limitations` now explains unavailable comparisons with rep numbers. Read `limitations`
and the original measurements; empty `issues` does not mean form was assessed as good.

Flags use existing `Issue` objects in both `rep.issues` and session `issues`. Each includes
actual values, reference rep numbers, threshold, and a simple review cue. IDs are deterministic
and unique within a response. All severities are `low` review priority, with `confidence: null`;
there is no validated probability to report. An `issue` timeline event points to that rep's
start and links its issue ID. Timeline remains chronological.

If any flags exist, `summary.primaryFocus` is `rep_consistency_review`, and the headline counts
measured changes flagged for review. Two flags on one rep count as two changes, not two bad
reps. All scores and `scoring` remain null. Do not derive a worst rep from flag count.

## Frontend and demonstration

B can integrate later using `contracts/examples/pushup-comparison-analysis.json`. It contains
three authored synthetic reps: first two take 1700 ms with 105° excursion; the third takes
3200 ms with 64° excursion. Its two flags have explicit supporting evidence. Keep its
**SYNTHETIC DEMO DATA** label; no matching recording exists.

Render flags as “Changes to review”, display the supplied explanation, and seek to
`issue.startMs / 1000` only when showing the actual matching uploaded video. The existing
one-rep push-up fixture and legacy squat fixture remain available. No frontend code was edited.

## Validation and next checkpoint

**Original failure, before v2:** [IMG_6942](REVIEW_6942.md) counts 4/4 and measures the slower third
rep, but its first two reference durations differ by 21.37%, exceeding the 20% stability gate.
No timing flag was produced during that initial validation. Policy v2 now flags rep 3 on the
same saved poses and keeps rep 4 unflagged. The four original clips retain 3/1/1/2 counts and
zero flags. Completed rep measurements/timestamps are unchanged across all five clips, and
cumulative/repeated-final replay and local coaching pass. Independent arithmetic checks each
flag against BOTH references. New tests cover variable references, both directional boundaries,
absolute floors, returning to prior pace, missing/timestamp-inconsistent durations and gaps.

Run from the repository root:

```bash
apps/api/.venv/bin/python -m pytest -q apps/api/tests/test_pushup_comparisons.py
```

Tests cover threshold boundaries/floors, both sides, missing/zero references, independent
stability gates, loss between reps, recovery, immutable inputs, cumulative replay, issue
links/order, and fixture/schema validation.

Replaying the saved real poses gives unchanged counts **3/1/1/2** and **zero flags**. The
one/two-rep clips have no eligible comparisons. For 6937 rep 3, the excursion comparison is
available but below its trigger; under v2 the duration comparison is available and its value
lies between the prior durations, so it is also unflagged. This does not establish good form.
No new pose extraction was needed. See VALIDATION.md for numerical evidence.

**Next:** validate v2 against a separate fixed-view recording before claiming
real-world detection reliability or choosing a form score. Use comfortable normal motion
and optional pauses; never ask someone to perform unsafe form to provoke a detector.
Evidence-only coaching can explain measured values while scoring remains deferred.

The replay checker now accepts exact expected flag rep numbers, or explicit zero flags,
for each rule independently. See [examples/README.md](examples/README.md#6-check-expected-comparison-flags).
It reports missing/extra flags and exits unsuccessfully on mismatches without changing any
input frames or thresholds. Synthetic positive checks pass; all four saved real-pose captures
pass explicit zero-flag checks with counts 3/1/1/2. IMG_6942 passes the expected rep-3 flag check
as a development regression. Separate real-footage validation is still pending.
