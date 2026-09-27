# Deliberately changed movement: badpushups.MOV

**Follow-up implemented:** independent body-line observations now identify review moments
even though this recording has zero completed reps. See MOVEMENT_OBSERVATIONS.md. The
original counting diagnosis below is unchanged; its missing-evidence discussion describes
the state before this addition.

Reviewed 2026-09-26 on push-up counter v2. The private recording is not committed.
The human describes about 4–5 attempts with torso/hip movement and little elbow bending;
the exact attempt count is uncertain. Treat that as a human annotation, not ground truth
for completed push-ups.

## Reproduction and evidence

From the repository folder containing `apps/`, with optional CV packages/model installed:

```bash
cd apps/api
.venv/bin/python -m app.tools.analyze_video ../../badpushups.MOV --output artifacts/review-badpushups
```

Outputs are private `poses.json` and `analysis.json` in that ignored artifacts directory.
Fresh native MediaPipe extraction produced:

| Observation | Result |
| --- | --- |
| Video | 3840 × 2160, 12,472 ms |
| Sampled frames | 188 |
| Selected elbow | Left; usable in 187 frames |
| Unavailable selected angle | One frame at 7,203 ms |
| Raw selected angle range | Approximately 98.7–179.7° |
| Raw samples at or below the 100° bend threshold | One, at 2,402 ms |
| Completed cycles | 0 |

The bend rule requires consecutive observations over at least 60 ms plus median confirmation.
One isolated sample cannot confirm a bend. The missing frame is not needed to explain why
no bend qualifies: even across all usable samples there is no sustained bend-zone sequence.
These are estimated 2D angles, not a calibrated judgment of push-up depth.

Manual frame review at 2.5 and 8 seconds shows the torso changing position with the lower
body close to the floor; elbow bending is visible too. The human's phrase “no elbows bending”
should not be copied into an automated finding. This manual review is not an implemented
form detector and does not establish an exact number of attempts.

## Why the coach has little specific feedback

The pretrained pose model estimates joints. Our code counts angle cycles and calculates
descriptive measurements. Current body-line measurements exist only inside completed reps.
With zero completed reps, that measurement list is empty. OpenAI receives the structured
evidence, not this video, so it cannot supply a missing hip/torso finding.

Zero completed cycles is compatible with visible movement. It neither classifies that
movement as bad form nor establishes a camera failure. Lowering thresholds until this clip
counts the human's estimated attempts would not implement form analysis.

## Next checkpoint

Analyze visible movement intervals even when no rep completes. First expose descriptive
observations and timestamps, check them against actual frames and normal examples, then
decide whether a specific review cue is supported. Keep completed reps distinct from
attempts, and retain null scores. An unsigned shoulder–hip–ankle angle alone cannot separate
sag from pike or measure spinal posture.

Keep this clip as a development example. Additional labeled clips help test generalization;
they are not automatically training data. Include normal motion and holds as well as changed
motion, and reserve separate footage for validation after any rule adjustment.
