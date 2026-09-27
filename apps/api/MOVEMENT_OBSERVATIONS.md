# Movement feedback outside counted reps

Policy `PUSHUP_BODY_LINE_BEND` / `1.0`, introduced September 26, 2026.
Purpose: describe something useful about visible movement even when no rep completes.
This is a provisional geometry review rule, not a calibrated form classifier.

## Measurement and availability

- Use the counter's selected anatomical side. Shoulder/hip/ankle must each pass the existing
  visibility >=0.7, image bounds and nondegenerate geometry checks.
- Measure raw unsigned shoulder–hip–ankle interior angle after restoring image pixel aspect
  ratio. 180° is straight. Require every sample <150° for >=500 ms, at least three samples.
- Require the shoulder-to-ankle direction to be predominantly horizontal: pixel |dx| >= |dy|,
  with nonzero dx. This filters common upright setup, not a verified exercise/camera view.
- Missing/low-visibility samples, ineligible direction, angle >=150°, or gaps >300 ms break
  the run. No filling missing samples, smoothing, or switching to the other body side.
- Emit chronological intervals with sample count, min/median/max angle and rule threshold.
  The median weights samples equally, not elapsed time. Do not round before eligibility checks.
- Cumulative live requests publish only closed intervals. Finalization closes the trailing
  interval if eligible. Earlier emitted intervals remain unchanged when more frames arrive.
- Rep counting, timing and existing per-rep metrics are unchanged. Count can be zero or unknown
  while an independent observation exists. No confidence probability or quality score.

The threshold is an explicitly uncalibrated hackathon heuristic. It may miss smaller bends
or flag setup, stretching and other movements. It cannot distinguish hip sag from pike,
measure spinal posture, explain why a rep did not count, or count attempts. Empty observations
do not establish good form. The app presents “Your body line bent here,” timestamps and an
expandable measurement explanation, not “bad reps detected.”

## Contract and coach

New default-empty `movementObservations` field in AnalysisResponse v1.0; see API_CONTRACT.md.
Schemas, generated TS and an explicitly synthetic zero-rep fixture are updated together.
New frontend accepts older omitted fields; old strict backend coach validators need updating.
Numeric observation cards go to conversational OpenAI and local summaries/count disputes.
No raw landmarks or video go to OpenAI. Other form conclusions remain unavailable.

## Development checks on existing recordings

| Recording | Completed reps retained | Observation intervals |
| --- | ---: | --- |
| IMG_6937 | 3 | none |
| IMG_6938 | 1 | 0.467–1.467 s; manual frame review shows a bent-body setup position |
| IMG_6939 | 1 | none |
| IMG_6940 | 2 | none |
| IMG_6942 | 4 | none |
| IMG_6943 | 19 | none |
| badpushups | 0 | 1.200–1.868, 3.335–3.868, 4.868–5.603, 8.803–9.472, 10.605–12.472 s |
| Blank video capture | unknown | none |

The five badpushups interval medians are about 132.4°, 128.9°, 123.2°, 130.2°, 138.4°.
Actual frames at 1.5, 3.6, 5.2, 9.1 and 11.5 s were inspected: visibly bent shoulder/hip/ankle
lines support descriptive review. **Five intervals do not establish five attempted reps.**
This clip motivated development; independent validation remains pending. The older setup
example is why wording deliberately allows non-exercise movement.

Fresh native multipart upload of badpushups returns the same five intervals as saved-pose
analysis. A real OpenAI HTTP question received a reply describing the 4.87–5.60 s bend with
matching evidence paths. Unit tests cover known geometry, side lock, aspect ratios/mirroring,
short runs/spikes, upright direction, tracking gaps, chronological live finalization, invalid
contract evidence, legacy omitted fields, and zero-rep local coaching. Frontend fixture and
evidence labeling tests accompany lint/type/build checks. No training or counting retuning.

Checkpoint checks: **447 backend tests, 53 frontend tests**, backend lint/format, both contract
checks, frontend lint/typecheck and production build pass. The existing Starlette TestClient
deprecation warning remains. These tests do not establish general camera/form accuracy.

Browser verification used a temporary development page rendering the real HTTP analysis:
all five intervals appeared, the 4.87–5.60 s button passed 4868 ms to the seek callback, and
the actual coach endpoint returned grounded local count-dispute feedback. Button spacing was
visually checked. The temporary page was removed. Browser file selection was restricted;
new end-to-end browser upload/video seeking was not verified in this checkpoint. Native HTTP
upload was verified separately, as described above. No browser permissions were changed.

Private data stays under ignored apps/api/artifacts and artifacts/count-investigation.
To see the change in an existing upload result, choose the file again and analyze it again;
old results do not acquire measurements automatically. Files moved/renamed after selection
must be selected again before uploading.
