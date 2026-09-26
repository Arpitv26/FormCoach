# Evidence-only coach

`POST /api/v1/coach` keeps the v1.0 request/response shape. It accepts an analysis and
`summary`, `next_set`, or `qa` (nonblank question required for QA). It is stateless.
No raw video or pose frames go to OpenAI. Computer A owns the implementation.

## Current implementation

1. `apps/api/app/services/coach_evidence.py` builds reviewed statements from numeric fields.
   It can describe a supplied score, completed count, push-up timestamps, observed elbow
   excursion, and corroborated comparisons against the two preceding reps.
2. `FallbackCoach` selects up to three statements locally. Review-flagged reps take priority;
   otherwise it starts with the first rep. The legacy scored fixture reports its supplied
   score. It never calculates a score. Local free-form QA is not implemented.
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

## Configuration and failures

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
