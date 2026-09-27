# AI coach

`POST /api/v1/coach` keeps the v1.0 request/response shape. It accepts an analysis and
`summary`, `next_set`, or `qa` (nonblank question required for QA). The server is stateless.
The current UI requests `responseStyle: "conversation"` and sends bounded recent history.
Omitting that field preserves the original `evidence` behavior described below.
Computer A owns the implementation. Optional upload visual review now sends sampled JPEG
frames to OpenAI, then attaches its findings to the analysis. Chat receives those findings
and numeric evidence, not the images again. Live capture remains numeric evidence only.

## Uploaded-video visual review

The human explicitly requested visual analysis after the numeric-only coach could not
identify obvious torso rocking. Enable with backend-only `VISUAL_REVIEW_ENABLED=true`,
`COACH_PROVIDER=openai` and `OPENAI_API_KEY`. `OPENAI_VISION_MODEL` defaults to
`gpt-5.4-2026-03-05`; Computer A also uses that snapshot for `OPENAI_MODEL`. Legacy chat's
default remains `gpt-4.1-mini-2025-04-14`. No keys or images enter frontend environment variables.

One native decode collects upright JPEGs no faster than 2 fps, then evenly retains at most
64 spanning the clip (960 px long edge, JPEG quality 80). A separate Responses request uses
image inputs, structured output, `store=False`, zero retries, an 80-second SDK deadline and
an 8,000-token cap; GPT-5.4 review uses medium reasoning. No new database or stored images.
User filenames and their GoodForm/BadForm labels are not sent to the model. The upload UI
discloses the sampled-frame request. Provider retention is governed by the account's terms;
`store=False` is not a zero-retention promise.

Findings identify an observation, an actionable cue, exercise/setup/finish phase and exact
sample references. Server code maps frame indices to timestamps and rejects invented
references. Results and chat label these as AI interpretation, separate from measured
angles/counts. Neither structured output nor correct citations proves visual accuracy.
The model must distinguish setup from working reps and avoid invented elbow tuck, forces,
muscle activation, injury risk and universal angle targets. Visual failures preserve measured
results and return `visualReview.status=unavailable`; disabled review is null.

GPT-5.4 development checks on press and normal/changed pulldown footage returned completed
reviews. The changed pulldown identified repeated torso recline/return and supplied a
steadier-lean cue, which a subsequent real chat used. Earlier GPT-4.1 drafts overinterpreted
setup/elbow position; those were not accepted as verified technique findings. This is a
small development check, not general visual coaching validation. Review timestamped claims.

### Follow-up: similar criticism on normal and exaggerated pulldowns

The human's browser rehearsal exposed overcorrection: the normal clip also received the
torso-rocking cue and an unsupported shortened-return claim. Inspection found no cross-clip
cache or filename-based answer selection. However, the original visual prompt explicitly
directed attention to torso rocking, supplied that wording as an example, and prioritized
1–3 adjustments. That was a leading instruction and inadequate visual validation.

The revised prompt has no example fault to imitate or correction quota. It assesses both
within-cycle movement and consistency across cycles, considers visible magnitude and
counterevidence, and permits positive/neutral findings with no correction. Missing a turning
point in <=2 fps samples cannot establish shortened range. Ordinary setup/finish transitions
are not defects. Chat must preserve an observation's magnitude/kind instead of escalating
slight motion into a fault. No exercise thresholds, counts, models or contracts changed.

Two repeated unlabeled reviews per clip on the 1080p images with original measurements
distinguished the normal set (consistent positions, slight/neutral motion) from the changed
set (larger within-pull recline and a correction). An earlier neutral draft undercalled one
changed-set review by confusing repeatable endpoints with steadiness within each rep; the
final prompt addresses that distinction. This remains development tuning on two clips,
not independent form-classification accuracy. New unit checks verify renaming GoodForm to
BadForm leaves provider input unchanged, different image content changes that input, and
replacing a completed upload clears its visual findings even with an identical filename.

Fresh original-file HTTP tests also deliberately swapped the multipart filename labels:
normal footage submitted as `BadForm.mov` returned 6 reps and positive/neutral findings with
no adjustment; changed footage submitted as `GoodForm.mov` returned 5 reps and an adjustment
for noticeable within-pull recline. No local recording was renamed. A real normal-set chat
summary preserved the small-motion description and did not repeat the shortened-return
claim. 550 backend/56 frontend tests, lint/format and TypeScript pass. These original uploads
and four repeated reviews are a small development evaluation, not a general accuracy claim.

**Latest addition:** independent `movementObservations` now supplies up to six timestamped
body-line bend cards, including zero-count and count-unavailable results. The model may explain
the observed shoulder–hip–ankle bend, not infer sag/pike, spinal posture, attempt count or the
reason reps failed to count. These may include setup. Local summaries and count-dispute replies
also mention an available interval. The full list remains visible in results. Existing
per-rep body-line medians retain their stricter rep-window availability rules.

One actual OpenAI HTTP check on the new badpushups analysis described a bend around 4.87–5.60 s
and cited that interval's measurements. This is one reviewed reply, not general QA validation.

## Conversation style (current UI)

The user asked for a friendly chatbot that explains their set and understands follow-ups.
`conversation_coach.py` now uses Responses structured output for short model-authored replies,
with reviewed numeric evidence cards and up to 12 user/assistant messages (2,000 characters
per message). The browser retains only the last six successful exchanges in memory. A new
set or reload clears them; no database or OpenAI conversation object is created.

- Usually 2–4 sentences; explicit rep breakdowns can be up to 900 words. Validation permits
  up to 1,000 words for QA and 200 for summary/next-set; the former 120-word rejection was
  unsuitable for detailed requests.
- Answers can explain measured differences or offer clearly general camera/pacing guidance.
- Conversation evidence prioritizes rep numbers in the current question, then recent user
  questions, before generic highlights. This keeps later reps (for example rep 12 of 19)
  available for direct questions and follow-ups within the six-rep input budget. Explicit
  numeric references such as `rep 12` or `reps 12 and 13` are supported. Questions containing
  each/every/all/breakdown/whole expand the input budget to 30 reps; otherwise six. This is
  bounded text matching, not full natural-language retrieval.
- Greetings should get a natural greeting, not another set summary. Zero counted reps means
  no completed cycles met the counting rules; it does not establish no movement, bad form,
  or camera failure. Specific visible technique claims require attached visual findings.
- User-reported reps and holds remain reports. Chat has measurements and any attached visual
  findings, not a continuous video stream.
- No invented form findings, scores, fatigue diagnosis, injury prediction or treatment.
- Structured output validates shape; known evidence IDs validate references. **Neither proves
  that every sentence is correct.** Model wording can be mistaken. Keep reviewing real replies.
- A targeted live evaluation exposed unsupported explanations of missed counts. Recognized
  count disputes and hold follow-ups now use brief local troubleshooting guidance, with no
  paid call, because completed-rep summaries cannot establish why unobserved reps were missed.
  This narrow text matcher is not a general semantic safety guarantee.
- Other questions use the configured OpenAI provider. Local free-form QA remains unavailable;
  failed calls say so. Local summaries and next-set camera guidance stay usable without a key.
- The response schema is unchanged. `provider: fallback` honestly identifies local guidance;
  `provider: openai` identifies generated wording. Evidence and brief limitations are expandable
  beside each message; the full analysis limitations remain in the results accordion.
- 35-second SDK timeout, 40-second overall deadline, zero retries, 3,500 output-token cap.
  Frontend chat waits 50 seconds; upload waits 300 seconds for pose plus visual processing.
  Placeholder analyses skip the provider. Calls happen only after a user action.
- Chat receives numeric and optional visual evidence cards, status/provenance, mode/question and recent text
  history. No video, raw landmarks, session ID, arbitrary analysis headlines or API key are
  included in the prompt. Questions/history can contain personal information. `store=False`
  does not promise zero retention.

Both styles use the backend provider/key/model settings in COACH_SETUP.md. Update the API
before using the new frontend: old strict v1 validators reject the additive request fields.
See the [conversation-state guide](https://developers.openai.com/api/docs/guides/conversation-state)
and [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Evidence style (legacy default)

1. `apps/api/app/services/coach_evidence.py` builds reviewed statements from numeric fields.
   It can describe a supplied score, completed count, push-up timestamps, observed elbow
   excursion, corroborated comparisons against the two preceding reps, and descriptive
   shoulder–hip–ankle medians with consistent sample metadata.
2. `FallbackCoach` selects up to three statements locally. Review-flagged reps take priority;
   otherwise it starts with the first rep. The legacy scored fixture reports its supplied
   score. It never calculates a score. Local free-form QA is not implemented.
   For `next_set` without review flags, one available body-line statement can replace the
   third statement. Existing timing/range review flags retain priority.
3. Optional `OpenAISelector` uses the Responses API with structured output to select up to
   three statement IDs. `OpenAICoach` validates the IDs, uniqueness, answerability, and response
   completion. The server renders the selected statements; **model-authored prose is never
   displayed**. This is constrained evidence selection, not an unrestricted conversational coach.
4. Every response retains synthetic/placeholder labels, missing-score information, partial
   analysis warnings, camera limits, and unknown-confidence warnings. Frontend must display
   `limitations` with `message` and label `provider` honestly.

The model receives at most six reps' statements, prioritized by review flags, then first/last
and remaining reps. Questions outside these available statements should be declined. QA
relevance still depends on the model and is not guaranteed. A model selecting a valid but
irrelevant statement cannot introduce new wording or findings.

## Evidence and limits

- `evidence` contains dot paths into the supplied AnalysisResponse; arrays use zero-based
  indexes, e.g. `reps.2.measurements.smoothedLeftElbowExcursionDeg`.
- Rep duration comes from end minus start timestamps. Excursion must match max minus min,
  with angles inside 0–180 degrees. Comparison medians/deltas must agree with the actual
  two preceding reps and declared reference numbers. Inconsistent comparisons are omitted.
- Body-line evidence requires a 0–180 degree median, integer sample count from 3–1800,
  usable count equal to total, a consistent same-side elbow range, and no competing opposite-side
  median. Absent/invalid keys omit the statement rather than repairing the values. The coach
  cannot recompute the median, sample gaps or visibility from AnalysisResponse alone.
  It describes unsigned 2D geometry and explicitly says it cannot distinguish hip sag/pike
  or judge form. Medians can hide brief changes. No corrective alignment cue is generated.
- The coach does not repeat arbitrary headlines, issue explanations, or cues as advice.
  It prioritizes reps containing issues but describes their numeric measurements only.
- It does not rerun visibility checks or recalibrate thresholds. Supplied measurements
  cannot prove camera origin: the endpoint accepts client-authored JSON. Do not describe
  this as tamper-proof validation or medically validated analysis.
- No invented biomechanics, quality scores, fatigue findings, diagnosis, injury prediction,
  or injury-prevention claims. Timing includes pauses/confirmation delay; angles are 2D.
- `next_set` adds a simple consistent-camera cue. It does not prescribe a movement correction
  unsupported by the current analyzer. No-flag results do not mean perfect form.
- Analysis/camera limitations are preserved as input text. Render all text as plain text,
  never injected HTML, and do not treat limitations as model-generated coaching.

## Legacy evidence-style configuration and failures

Default `COACH_PROVIDER=fallback` makes no paid calls, even if a key is present.
Optional setup requires **both** `COACH_PROVIDER=openai` and a backend-only API key,
plus `requirements-coach.txt`. Instructions: [COACH_SETUP.md](../apps/api/COACH_SETUP.md).
The default model is the fixed `gpt-4.1-mini-2025-04-14` snapshot; one live request verified account access
on Computer A on 2026-09-26. `OPENAI_MODEL` can override it with a model supporting
Responses structured output. Do not put keys in frontend variables.

The adapter uses an 8-second SDK timeout, a 10-second overall selection deadline, zero
retries, and 300 maximum output tokens. Missing SDK/key, refusal, incomplete response,
rate limit, invalid selection, timeout, or API error yields `provider: "fallback"` and a
safe limitation. No provider exception or credential is returned. No evidence/placeholder
input avoids the call entirely. Disable with `COACH_PROVIDER=fallback` and restart the API.

`store=False` is sent. This is not a zero-retention guarantee. Only reviewed numeric
statements, mode, and (for QA) the user's question are sent; no session ID, analysis prose,
video, or landmarks. Questions themselves may contain user-entered personal information.

## Validation checkpoint

- Conversation retrieval follow-up (2026-09-26): 428 backend tests pass. Requested later reps,
  follow-up context, nonexistent rep references and a zero-result greeting have regression
  tests. One actual HTTP request using the saved IMG_6943 analysis asked for rep 12's duration:
  `provider: openai`, reply “Rep 12 took 1.14 seconds from start to finish, including pauses.”
  Returned evidence references the matching rep's numeric fields. This verifies the configured
  provider and that one answer; it does not prove general conversational or form accuracy.
  Prompt instructions now explicitly distinguish unassessed form from absent faults and
  avoid turning every zero-result reply into a request for another recording.

- Timing v2: local next-set feedback for IMG_6942 prioritizes the new rep-3 review issue and
  explains 3.07 s versus the preceding median 1.57 s (+1.50 s). Evidence paths resolve to
  numeric data; all five saved clips pass local coach route checks. No selector/SDK changes
  or paid requests. Missing-comparison reasons pass through existing `limitations`.

- Body-line follow-up: all seven reps in the four saved real analyses produce evidence cards;
  local `next_set` requests for each clip pass through HTTP handling and retain camera limits.
  Evidence paths resolve to supplied numeric values. Invalid/partial metadata, opposite-side
  conflicts, 0/180-degree boundaries, synthetic labels and review-flag priority have tests.
  A simulated selector verifies body-line QA rendering; no live model-relevance check was
  made for this new card. No paid API call was used for this checkpoint.

- Local fallback checked through the route against all four saved measured analyses:
  counts 3/1/1/2; no fabricated score or positive form claim.
- Synthetic three-rep comparison explains 3.20 s versus 1.70 s, and 64° versus 105°;
  it is labeled demo data. Real positive comparison validation remains pending.
- Tests cover evidence paths, malformed measurements, injected prose, partial/camera
  limits, key gating, unsupported questions, invalid selections, deadline cancellation,
  and the installed SDK parsing simulated HTTP success/refusal/error responses.
- **Live check passed on 2026-09-26:** after saving a backend-only key and enabling
  `COACH_PROVIDER=openai`, called the actual coaching service once with the synthetic
  comparison fixture and “How long did rep 3 take?”. The result used `provider: openai`,
  took 3.22 seconds, and selected rep-3 timing evidence: 3.20 s versus the reference median
  1.70 s. Demo labeling and unknown score remained intact. No key was displayed or committed.
  This verifies one service-level network request, not frontend integration, general QA
  relevance, real-video accuracy, or a latency guarantee. No billing amount was checked.

## Official references

The implementation uses the SDK's Pydantic `responses.parse` path documented in
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
The chosen model supports Responses and structured output; see the
[GPT-4.1 mini model page](https://developers.openai.com/api/docs/models/gpt-4.1-mini).
Review [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data)
before making privacy claims.
