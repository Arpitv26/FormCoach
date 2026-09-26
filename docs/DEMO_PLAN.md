# Demo plan

**Live reliability matters more than implementing 20 exercises.** This describes the intended
demo after feature work; the bootstrap alone does not perform movement analysis.

## Live sequence

1. Open the camera experience and let the participant get into frame.
2. Show honest camera readiness: needed joints visible and a usable view.
3. Select squat. Say “detected” only if automatic recognition was actually implemented.
4. Perform several comfortable good reps; show the skeleton and live completed-rep count.
5. Perform one comfortable, visibly inconsistent rep (for example a tempo or range change).
   Choose a variation supported by the real implemented rules and camera view.
6. Show the measured cue with its confidence/visibility context.
7. Finish the set. The dashboard shows overall score, available metrics, rep scores,
   lowest-scoring rep, and issue timeline.
8. Explain one concrete measurement and how it produced a rule/score.
9. Ask the coach for a concise explanation grounded in that structured evidence.
10. If synchronized video exists, jump to the worst rep or issue moment.

The synthetic fixture includes a knee-tracking issue around rep 5 for UI work. Do not assume
the first real side-view squat analyzer can measure that same issue. Rehearse a truthful
demonstration of the implemented detector rather than forcing the footage to match the fixture.

## Recorded gym path

Use consented videos filmed at Anytime Fitness, subject to gym recording rules. Keep
bystanders out of frame. Select the exercise and view that the implemented backend supports.
Equipment exercise options include barbell squat, curl, shoulder press, and deadlift, but
none are working in bootstrap. Use a short clip and annotated playback with synchronized
rep boundaries, pose overlay, and issue highlights after that feature is implemented.

## Rehearsal and fallback order

- Confirm the correct branches are integrated, dependencies installed, battery charged,
  camera permission granted, lens unobstructed, and both servers running.
- Pick the camera orientation and distance supported by the chosen rule. Test venue lighting.
- Rehearse start → good reps → supported variation → finish → results at least twice.
- Keep one consented short recording and its genuinely computed result for a measured fallback.
- If live or recorded analysis fails, openly switch to the labeled synthetic UI walkthrough.
  Do not pretend it is a result from the current participant.
- The local coach fallback keeps the UI usable without network/API credits. Label its provider.
- Avoid dependency upgrades or last-minute contract changes before presenting.

## Pitch and judging

| Judging area | What to demonstrate |
| --- | --- |
| Functionality — 35% | A repeatable camera-to-analysis flow, rep count, grounded issue, working fallback |
| Pitch & communication — 25% | Clear problem, one user story, concise limitations, visible before/after value |
| Technical complexity — 20% | Shared PoseFrame pipeline, custom phase/rep logic, measurement-derived scores, evidence-only AI |
| UX & design — 20% | Framing guidance, clear feedback, polished results, meaningful playback/graphs |

Suggested pitch arc: ordinary camera → structured body landmarks → our measurement and
rep logic → explainable result → coach explains evidence. Be clear that the pose model is
pretrained and the team's contribution is movement interpretation and the product experience.
