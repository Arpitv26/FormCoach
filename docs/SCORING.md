# Scoring principles

A score must have an understandable path back to measurements. Real scoring is **not
implemented in bootstrap**. Never report a random score, a pretend ML confidence, or 100
because a rule could not run. Domain `null` becomes a visible “Not available” state in the UI.

## Planned measurement path

1. Establish camera orientation, visibility, and sufficient usable samples.
2. Derive measurements per completed rep (angles, timing, displacement, left/right differences).
3. Convert each supported measurement to a documented metric score using calibrated thresholds.
4. Combine available metrics according to the exercise's declared scoring policy.
5. Expose the scoring version, weights, concrete measurements, and limitations.

The example squat profile proposes ROM 0.30, symmetry 0.20, tempo 0.15, stability 0.20,
consistency 0.15. These weights sum to 1 and are hackathon heuristics. They are not a
validated medical scale and should not imply false precision or universal exercise support.

## Exact synthetic fixture arithmetic

The six-rep fixture has authored metric inputs and illustrative joint angles. **Its angles
do not generate its metric inputs.** Do not use this example as training data or claim the
numbers came from a video. It exists to build and test the dashboard.

| Rep | ROM | Symmetry | Tempo | Stability | Weighted rep score |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 94 | 92 | 90 | 96 | 93.3 |
| 2 | 92 | 90 | 88 | 94 | 91.3 |
| 3 | 88 | 86 | 84 | 90 | 87.3 |
| 4 | 78 | 78 | 76 | 86 | 79.5 |
| 5 | 64 | 54 | 62 | 68 | 62.2 |
| 6 | 86 | 84 | 80 | 88 | 84.9 |

Each rep score is `(0.30*ROM + 0.20*symmetry + 0.15*tempo + 0.20*stability) / 0.85`,
rounded to one decimal. Consistency is set-level, so it is deliberately excluded from every
rep's metric set. This planned exclusion differs from silently dropping missing measurements.

Session ROM/symmetry/tempo/stability are each the arithmetic mean of six inputs, rounded
to one decimal: **83.7, 80.7, 80.0, 87.0**. Demo consistency is
`max(0, 100 - (highestRepScore - lowestRepScore))` = **68.9**. The overall score is the
weighted sum of these five rounded session metrics, rounded to one decimal: **81.0**.
This intentionally simple example is not a validated fatigue metric. Tests check this arithmetic.

The knee-tracking issue is authored for rep 5. Camera quality 0.91 and issue confidence 0.87
are also synthetic UI inputs, not inferred confidence estimates. Exercise confidence is null
because “squat” was selected rather than recognized. The fixture explicitly warns that one
real camera view may not support every illustrated metric simultaneously.

## Missing or unreliable data

For real scoring, define which metrics a specific camera view supports before the set.
If a required metric has insufficient evidence, return its score as null and explain why.
Until a calibrated missing-data policy exists, return null for an aggregate that depends
on any unavailable required metric. Do not silently renormalize around missing metrics.
An intentional profile/view-specific metric set can have different weights, but must expose
that scoring version and avoid comparing it directly with a different scoring setup.

Lower/unknown measurement confidence must remain visible; a high form score cannot hide a
poor camera view. `cameraQuality.score` is a view-quality estimate, not the overall form score.
Unknown analysis has null totalReps, while a reliable observation of zero completed reps may
use zero. Use `insufficient_data` when evidence is inadequate and `not_implemented` for stubs.
