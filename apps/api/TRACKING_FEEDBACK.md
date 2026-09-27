# Tracking coverage and missing-joint feedback

The analyzer now explains observation coverage in the existing `cameraQuality.issues`
strings. Both live requests and uploaded video use this code. The v1.0 schema, generated
types, rep segmentation, measurements and scoring behavior are unchanged.

## What is reported

- Selected elbow/knee angle: usable samples out of all received samples.
- Each blocked required joint: counts of not detected, outside image, unknown visibility,
  and low estimated visibility, followed by a framing/visibility cue.
- Undefined angles caused by coincident joint positions, separately from visibility.
- For push-ups with a selected side: samples where shoulder, hip and ankle all pass
  visibility checks together. Missing hip/ankle feedback does **not** block elbow counting.
- Before any side is usable: both candidate triplets are explained. An empty request says
  coverage is unknown; it does not produce a zero-percent rating.

Example diagnostic for a synthetic occlusion case:

```text
Left wrist unavailable in 4 of 25 sampled frames (1 not detected, 1 outside the image,
1 visibility unknown, 1 low estimated visibility). Adjust framing to keep this joint
inside the image.
```

`tracking_feedback.py` reuses the geometry/visibility gates. Each joint has at most one
reason per sample, with precedence missing → outside → unknown → low. Different joints
can fail in the same frame; their counts must not be added to get unavailable frame totals.
Unknown visibility never counts as visible. Threshold is the exercise profile's existing
0.7 heuristic, not a calibrated probability of correct tracking.

The report uses the counter's locked anatomical side and the entire received sequence.
If selection happens later, earlier frames are checked against that eventual side too.
It never switches sides to improve reported coverage, and never feeds back into counting.

## Interpretation and UI handoff

These are **sample counts**, not elapsed-time coverage, current readiness, form scores,
or camera-angle validation. Irregular sampling or a long time gap can still yield usable
angles in every received frame while the counter correctly discards an interrupted rep.
The existing tracking-break limitation explains that case.

Passing shoulder/hip/ankle visibility does not establish full-body visibility or alignment.
`cameraQuality.score`, `fullBodyVisible`, all quality scores and scoring metadata remain null.
There are no new exercise issue flags or coaching evidence cards in this checkpoint.

B can continue rendering `cameraQuality.issues` as text in its existing visibility/details
section. Despite its historical name, that array also contains coverage information and
limitations. Do not treat its length as a failure count, turn every entry into a red warning,
or parse the prose for numeric charts. Structured coverage would be a separate coordinated
contract addition. The coach retains these diagnostics in limitations.

## Verification — 2026-09-26

**311 backend tests pass.** New cases cover reason aggregation, side selection before/after
locking, missing body joints, simultaneous visibility, degenerate geometry, empty input,
and gaps even when sampled-frame coverage is complete. Existing failure/recovery and
schema tests still pass. Lint, format and schema checks pass.

Saved real poses were replayed through HTTP route handling, with cumulative snapshots and
a repeated final request. Rep objects, summary, issues, timeline, metrics, status and scoring
match the prior comparison checkpoint exactly:

| Clip | Human / observed reps | Side | Elbow-angle samples | Shoulder/hip/ankle samples |
| --- | --- | --- | --- | --- |
| IMG_6937 | 3 / 3 | Left | 287 / 287 | 287 / 287 |
| IMG_6938 | 1 / 1 | Left | 53 / 53 | 53 / 53 |
| IMG_6939 | 1 / 1 | Left | 46 / 46 | 46 / 46 |
| IMG_6940 | 2 / 2 | Right | 104 / 104 | 104 / 104 |

No new native extraction or OpenAI call was needed. These clips do not validate diagnostics
on real occlusions; those failure cases are tested synthetically. Local reports remain ignored
under `apps/api/artifacts/tracking-check/`. Real positive comparison validation is still pending.

To run the focused checks, open Terminal at the repository root and paste:

```bash
cd apps/api
.venv/bin/python -m pytest -q tests/test_tracking_feedback.py tests/test_pushup_analysis.py tests/test_live_analysis.py
```

Expected: **53 passed**. To see updated feedback in the app, use the updated running backend
and analyze the clip again; an old browser result does not update by itself.
