# Product behavior and claims

FormCoach provides general movement feedback. It does not diagnose injuries or medical
conditions, predict injury, or replace qualified medical or fitness professionals.

## Evidence and uncertainty

Computer vision can miss joints, confuse left/right, or estimate points through occlusion.
Camera orientation, lighting, clothing, equipment, and a partly visible body can make a
measurement unreliable. Estimated depth is not calibrated 3D. The analyzer must gate rules
on adequate evidence and the UI must show confidence/visibility limitations.

“Not enough information from this angle” is a valid result. Unknowns must not become zero,
perfect scores, invented detections, or an AI-generated substitute finding. A model's landmark
visibility score is not a medical confidence score. Heuristic weights/thresholds need calibration.

## Appropriate product language

Use concrete observations such as “In the measured view, rep 5 had less range of motion”
only when the corresponding measurement exists. Use concise grounded cues. Do not claim
“this will injure your knee”, “this prevents injury”, or label an observed pattern a diagnosis.
Issue severity communicates coaching priority, not health risk. Do not interpret a declining
score chart as proof of physiological fatigue.

Keep the UI calm: a small general-feedback note and contextual uncertainty messages are
enough. Show framing help where it is useful, rather than a wall of warning text.

## Demo data and recording

Synthetic data must remain visibly labeled, including coach responses. Do not imply a
recording was analyzed when the screen is rendering the fixture. If the live analyzer fails,
announce switching to a prerecorded measured example or a synthetic UI walkthrough.

Get consent before filming participants. Follow the gym's recording rules and keep bystanders
out of frame. Do not commit recordings to Git. Bootstrap has no persistent storage; browser
camera capture and explicit recording controls are future frontend work.

For the inconsistent-rep demo, choose a comfortable unloaded variation in tempo or range
that the implemented rule can measure. Do not ask someone to exaggerate a painful or unsafe
movement to trigger a detector. Stop activity if the participant reports pain.
