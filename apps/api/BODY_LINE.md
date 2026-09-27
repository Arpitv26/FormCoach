# Push-up body-line measurement

This checkpoint adds descriptive shoulder–hip–ankle geometry to each completed push-up's
existing `measurements` dictionary. It uses the same anatomical side as elbow counting.
No schema, generated type, rep rule, score or issue-code change is required.

## Definition

Measure the unsigned interior angle at the hip between shoulder and ankle, using image
coordinates scaled back to equal-size pixel axes. Take the median of the **raw** angles
sampled within `rep.startMs <= timestampMs <= rep.endMs`, inclusive. This differs from the
elbow extrema's smoothed signal and descent-confirmation window. Depth is unused.

| Measurement key | Units / meaning |
| --- | --- |
| `medianLeftShoulderHipAnkleAngleDeg` / `medianRightShoulderHipAnkleAngleDeg` | Median angle in degrees, 0–180, or null; only the selected side is emitted |
| `bodyLineSampleCount` | Number of received frames inside the counted rep interval |
| `bodyLineUsableSampleCount` | Number with an available shoulder–hip–ankle angle |

Each angle requires all three joints in-frame, visibility >= the profile's 0.7 heuristic,
and noncoincident segment endpoints. Missing visibility is unavailable. A real zero-degree
angle is distinct from unavailable geometry.

The median requires **all** interval samples usable, at least three samples, observations
at both rep boundaries and no intersample gap over 300 ms. Otherwise it is null. These are
conservative engineering availability rules, not a calibrated accuracy guarantee. Sample
counts remain available so partial coverage is not hidden. No interpolation or side switching.
Body-line tracking loss never deletes an elbow-counted rep. Each subsequent rep can recover.

## Interpretation

180 degrees describes three collinear image points with the hip between shoulder and ankle.
It is not a target or a form score. This unsigned angle cannot distinguish hip sag from pike,
evaluate spinal posture, verify a side view, or establish injury risk. Clothing, perspective,
and model estimates affect it. Do not rank recordings from different views with these values.

The median weights samples equally, not elapsed time. It can hide a short deviation and is
not peak misalignment, stability, or a fatigue measure. A good/bad threshold and corrective
cue are deliberately not introduced without separate validation. Existing comparison flags
still use elbow excursion and counted time only. Existing coach evidence cards do not yet
explain this new measurement; they continue explaining their supported timing/range evidence.

## Frontend handoff

Contract remains v1.0. Older responses/fixtures may lack these dictionary keys: show unknown
or omit the display, never turn missing/null into zero. Suggested label:
**Median shoulder–hip–ankle angle (2D)**. Use one decimal place, retain the selected-side label,
and keep the interpretation above accessible. No ideal-angle colour scale or worst-form ranking.

`contracts/examples/pushup-analysis.json` now includes an explicitly synthetic 160-degree
example with 18/18 usable samples. Its values match authored test geometry; it has no video.
B's current components can ignore the additive keys. Rendering this metric can be included
in A's later visual overhaul without delaying B's current coach/live-counting work.

## Validation — 2026-09-26

335 backend tests and 35 frontend tests pass, with lint, formatting, schema/type checks and
the production frontend build. The existing Starlette TestClient deprecation warning remains.

Known synthetic angles, left/right, aspect ratios, mirroring, missing/low/unknown visibility,
offscreen/coincident joints, sparse intervals, missing boundaries and independent rep recovery
are tested. Completed results remain unchanged when later frames arrive. The fixture validates
against the existing schema and matches the synthetic calculation.

Four saved real pose captures were replayed through HTTP route handling. Counts remain
3/1/1/2; all earlier measurement values, timestamps, issues, summary and status match the
tracking-feedback checkpoint. All seven new medians match an independent dot-product/arccos
calculation within 1e-8 degrees. This checks implementation arithmetic, not anatomical accuracy.

| Clip / rep | Selected side | Usable / received samples | Median angle |
| --- | --- | --- | --- |
| 6937 / 1 | Left | 39 / 39 | 177.7° |
| 6937 / 2 | Left | 30 / 30 | 178.4° |
| 6937 / 3 | Left | 36 / 36 | 174.8° |
| 6938 / 1 | Left | 31 / 31 | 155.8° |
| 6939 / 1 | Left | 31 / 31 | 161.6° |
| 6940 / 1 | Right | 31 / 31 | 167.4° |
| 6940 / 2 | Right | 32 / 32 | 166.4° |

One frame near the median for each rep was decoded from the original video using its source
frame index; timestamps agreed within 35 ms. The shoulder–hip–ankle line was plotted over
those seven actual frames and visually inspected, including portrait rotation. Points align
plausibly with the image, but there is no manual landmark ground truth or calibrated form label.
The different clips/views are not a quality ranking. Real occlusion and positive form-change
validation remain pending; do not extrapolate accuracy from these four recordings.

Private plots, reports and the local review script remain ignored in
`apps/api/artifacts/body-line-check/`; they contain participant footage and are not in Git.
No new native pose inference or OpenAI request was needed.

From the repository root, run:

```bash
cd apps/api
.venv/bin/python -m pytest -q tests/test_pushup_body_line.py
```

Reanalyze a clip to get the new keys. A previously displayed browser result will not update
automatically, and the current UI has not yet added a dedicated body-line card.
