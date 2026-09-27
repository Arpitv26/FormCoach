# Live rehearsal correction — 2026-09-26

## What failed

**Later captured failure and correction:** see [COUNTING.md](../apps/api/COUNTING.md).
The new saved live request reproduced 4 and now returns 5; IMG_6943 reproduced 5 and now
returns 19 observed cycles. Counter v2 supersedes the counting policy described below.
The display fix is retained. Reported 20 versus reviewed 19 and a physical live retest
remain open; the earlier synthetic check is not proof of camera accuracy.

The human performed **five push-ups**, including about seven seconds at the bottom of the
fourth. The live page reported **two**, with 210 sampled frames, 208 usable right-elbow
samples and two tracking breaks. Detected intervals were 10.42–14.85 s and 18.99–21.32 s.
This is a failed physical rehearsal. There is no recording or exported raw capture of that
set. Visible aggregate measurements cannot establish why three reps were missed.

## What changed

1. **Live input:** a stale display previously emitted `onFrame(null)` just before a valid
   pose. The 100 ms sampling throttle could accept the false missing observation and discard
   the valid one. Staleness now clears only the display. Actual no-person observations and
   elapsed timestamp gaps still reach the analyzer. This is a concrete bug fix, not proof
   that it explains the entire five-to-two failure. No counting thresholds changed.
2. **Replay:** after a final set, “Count look wrong?” downloads the exact sampled landmark
   request. It contains no video or key. It stays in memory until explicitly downloaded;
   resetting/reloading loses it. Keep captures private and out of Git.
3. **Coach:** short conversational OpenAI replies with bounded recent history; expandable
   measurements. Targeted model checks exposed speculative explanations for missing reps,
   so recognized count disputes/hold follow-ups use honest local troubleshooting guidance.
   Other questions remain conversational. See AI_COACH.md for data flow and limitations.
4. **Flow:** enable → start → finish → summary/chat → optional rep details. Finishing releases
   the camera; setup/duplicate live stats disappear from results. The chat is scrollable,
   and detailed measurements, flag reasoning and limitations are collapsed by default.

## UX review from the supplied screenshots

| Step | Health at reported failure | Correction / remaining check |
| --- | --- | --- |
| 1. Capture and finish | Failed count; camera continued running after final response | Display/input separation and automatic camera release; physical retest required |
| 2. Results | Duplicate count panels, setup beside completed set, weak partial-result message | One result section; prominent incomplete-count message; clear new-set action |
| 3. Compare reps | Useful timestamps and bars, too much technical prose | Chart links reveal the rep accordion; detailed flag reasoning collapses |
| 4. Coach | Selected evidence read like a technical report; no conversational memory | Short chat replies, recent history, ordinary message composer and expandable evidence |

Screenshots alone cannot verify count accuracy, screen-reader behavior or color contrast.
The new synthetic UI check confirms local summary, count troubleshooting, chart → rep details,
collapsed sections and a 390 px layout with no horizontal overflow. Keyboard-visible focus,
labeled controls and a focusable chat log are retained; no full accessibility certification.
Private test screenshots are under ignored `artifacts/rehearsal-fix/` in the review checkout.
The temporary synthetic preview route is removed before committing.

## Checks and limits

412 backend tests and 52 frontend tests pass; lint, format and generated contracts pass.

- Backend and frontend unit tests cover the stale-display regression, exact/deep-copied
  export, five synthetic cycles with a seven-second fourth-rep hold, conversation history,
  evidence validation, local missed-count replies and provider failures.
- A synthetic long-hold test counts five under the existing thresholds. It does not reproduce
  the user's physical landmarks or prove the reported counting failure is fixed.
- Two real OpenAI requests using synthetic comparison data verified generated wording and
  a simpler follow-up retaining the earlier context. Earlier model probes revealed unsupported
  missed-count explanations and motivated the local routing above. No personal video was sent.
- Real video upload in the browser could not be repeated in this check because the browser
  extension lacked file access. The isolated UI was instead checked against labeled synthetic
  data and the real local coach API. This does not replace a real upload or webcam rehearsal.

## Next human check (no terminal needed)

1. Refresh the updated camera page. Keep the backend and frontend terminals running.
2. Enable the camera and wait for the skeleton. Use a side view with one person in frame.
3. Press **Start set**, do five comfortable push-ups, then press **Finish set**.
4. Compare the detected count with five. Before starting another set, open **Count look wrong?**
   and press **Download troubleshooting data**, even if the count is correct.
5. Share the downloaded file's local path with the coding agent. Do not commit it or put it
   in a public issue. We will replay those exact observations and inspect missed transitions.
6. Try **How did my set go?**, then ask a follow-up. AI requires the existing backend OpenAI
   settings; local summaries and count troubleshooting also work without a key.

The next development checkpoint is accurate counting on this captured physical rehearsal,
then the larger visual overhaul. Scores, diagnosis, automatic exercise recognition and
other gym analyzers remain outside this fix.
