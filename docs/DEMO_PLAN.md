# Demo plan

**Updated user direction: prerecorded push-ups, no squat demo.** Reliability on the actual
gym clip matters more than live camera tracking or implementing many exercises. Computer B
is still building the frontend; Computer A owns video pose extraction and movement analysis.

## Main sequence — prerecorded gym video

1. Select a consented short side-view push-up clip and explicitly select `push-up`.
2. Extract poses using a pretrained model; show the skeleton once that UI is implemented.
3. Run the same movement analyzer used for live pose batches.
4. Show completed-rep counts, elbow-angle measurements, and rep intervals.
5. Seek to corresponding moments in that same clip. Compare against a human count.
6. Add only genuinely implemented metrics/issues. Scores remain unavailable until grounded
   scoring exists; an empty issue list is not proof of good form.
7. Explain one actual measurement, and later let the AI coach summarize that evidence.

Local backend video extraction and push-up counting match human counts across four supplied
recordings (3, 1, 1, 2); see apps/api/VALIDATION.md. HTTP uploads are wired; UI playback
validation and timeout integration are next (apps/api/HTTP_UPLOAD.md). No body-alignment or form-score accuracy is claimed yet.
The old six-rep squat fixture must not be relabeled as push-up results.

## Recording and acceptance

Film at Anytime Fitness only with permission under its rules; avoid bystanders. Keep the
camera fixed and side-on with shoulder, elbow, wrist, hip, and ankle visible. Start and end
with a brief straight-arm top pause. Use 3–5 comfortable repetitions for the first clip.
Keep the recording in an ignored local `artifacts/` folder, not Git.

Record human count, observed count, missed/extra reps, timing differences, and visibility
problems. A matching total alone does not prove that each rep was identified correctly.
See apps/api/examples/README.md for the pose replay tool. Confirm actual clip results before
adding variation demonstrations or making accuracy claims.

## Later live option and fallback

Browser tracking is later work on Computer B. It will send the same pose contract; it should
not block the recorded demo. Rehearse the recorded flow twice on the presentation machine.
Keep a successfully analyzed local clip and its matching measured results. If processing
fails, label any synthetic walkthrough explicitly. The local coach fallback does not need a key.
Freeze working dependencies/contracts before the pitch.

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
