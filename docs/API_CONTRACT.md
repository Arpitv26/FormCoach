# API contract v1.0

**Freeze this boundary before parallel feature work.** All routes are under `/api/v1`.
Development base URL: `http://localhost:8000`. JSON uses camelCase and milliseconds.
The payload field is `contractVersion: "1.0"`; this is separate from the app/package version.
All responses with analysis or coaching include it. Health is intentionally smaller.

Canonical sources: `apps/api/app/domain/` models, generated `contracts/*.schema.json`,
generated `apps/web/src/lib/api/types.ts`, and fixtures under `contracts/examples/`.
Interactive route docs: http://localhost:8000/docs. Do not hand-edit generated files.

## Ground rules

- Scores are 0–100; confidence, visibility, and camera quality are 0–1.
- `null` means unknown/unavailable; `0` is an actual zero. Never use NaN or Infinity.
- Analysis output fields are present, including explicit null values. Request fields with
  defaults may be omitted. Avoid relying on omission to mean a different kind of unknown.
- `status`: `complete`, `partial`, `insufficient_data`, or `not_implemented`.
- `provenance.kind`: `measured`, `synthetic`, or `placeholder`. Always expose synthetic labels.
- Empty issue lists do not prove good form when analysis is unavailable.
- `limitations` explains missing scores, uncalibrated heuristics, view limits, or unavailable features.
- Push-up and squat counting from supplied poses is implemented; four real push-up clips
  match human counts. This is not a general accuracy benchmark.
  Other exercise profiles describe planned capability. Push-ups support descriptive timing/range
  comparison flags; scores and biomechanical form assessment remain unavailable.
- Extra fields are rejected by the backend models. Coordinate shared additions deliberately.

## GET /api/v1/health

HTTP 200:

```json
{"status":"ok","service":"formcoach-api"}
```

This means the API process responds, not that pose tracking or OpenAI is ready.

## PoseFrame and coordinates

```typescript
type PoseLandmark = {
  index: number;       // integer 0–32; canonical mapping below
  name: string;        // must match index, e.g. left_knee = 25
  x: number;
  y: number;
  z?: number | null;
  visibility?: number | null;
};
type PoseFrame = {
  frameIndex: number;  // nonnegative source-frame index, allowed to skip frames
  timestampMs: number;
  landmarks: PoseLandmark[];
};
```

These are our types. Providers must map their own objects into them.

**Image plane:** origin is the top-left of the original, upright, unmirrored video frame.
`x = pixelX / imageWidth`, positive right. `y = pixelY / imageHeight`, positive down.
In-frame positions are normally 0–1. Finite out-of-frame values are allowed and must NOT
be clamped: a joint outside the image is not visible just because a model estimates it.
Widths/heights describe the image after rotating it upright. If inference uses a crop or
letterbox, map positions back into this full image before sending.

**Left/right:** always the person's anatomical left/right, never the viewer's. A webcam
preview may be mirrored with CSS, but frames sent to analysis remain unmirrored. Transform
the displayed skeleton with the preview, not the underlying contract coordinates.

**Aspect ratio:** x and y use different denominators. Before calculating a 2D angle, use
`(x * imageWidth, y * imageHeight)` or `(x, y * imageHeight / imageWidth)`; treating raw x/y
as equal-scale axes distorts angles on a non-square image.

**Depth:** optional `z` is relative depth with the hip midpoint as origin, smaller values
toward the camera, in units approximately equal to normalized image width. It is NOT meters.
If a provider cannot supply this convention, set `z: null`; do not insert its native meters.
Do not treat estimated relative z as calibrated 3D ground truth.

**Visibility:** estimated visibility in 0–1, not a calibrated probability of correct form.
Unknown visibility is null/omitted. It is not 1. Missing joints may be omitted; empty
`landmarks: []` means no pose detected in that frame. No duplicate indices or zero-filled
stand-ins. Frame timestamps/indices strictly increase within a request. Timestamps are
relative to the start of the set/clip, not Unix time, arrival time, or per-batch time.

Canonical 33-slot mapping (compatible with common pose models, independent of their SDK):

```text
0 nose                 11 left_shoulder       22 right_thumb
1 left_eye_inner       12 right_shoulder      23 left_hip
2 left_eye             13 left_elbow          24 right_hip
3 left_eye_outer       14 right_elbow         25 left_knee
4 right_eye_inner      15 left_wrist          26 right_knee
5 right_eye            16 right_wrist         27 left_ankle
6 right_eye_outer      17 left_pinky          28 right_ankle
7 left_ear             18 right_pinky         29 left_heel
8 right_ear            19 left_index          30 right_heel
9 mouth_left           20 right_index         31 left_foot_index
10 mouth_right         21 left_thumb          32 right_foot_index
```

## POST /api/v1/live/analyze-batch

Content-Type: `application/json`. Example: `contracts/examples/live-pose-batch.json`.
It is a tiny synthetic contract example, not a full squat recording.

| Field | Meaning |
| --- | --- |
| `contractVersion` | `"1.0"`; defaults to this if omitted |
| `sessionId` | Non-empty string up to 100 characters; frontend can use `crypto.randomUUID()` |
| `exerciseHint` | Optional registered exercise ID; null means no selection |
| `imageWidth`, `imageHeight` | Required positive integer dimensions, up to 16384 each |
| `frames` | Required cumulative sampled frames from this set; 0–1800 frames |
| `isFinal` | Defaults false; true means the set ended and no more frames will be added |

**Stateless protocol:** start a new session ID and clock at the start of a set. Sample up
to 15 frames/second for a set of at most 120 seconds. Send the complete accumulated
sampled sequence about once/second, with only one request in flight. Each response replaces
the dashboard's current analysis; do not add response rep counts together. Do not send
only the newest chunk, as that loses reps at batch boundaries. Re-sending the same snapshot
is safe. Abort or ignore an old response after switching sessions. Keep image dimensions
and exercise hint fixed within a session; reset if either changes. Gaps retain original
indices/timestamps; the analyzer resets unfinished reps across tracking gaps, without interpolation.

When the user ends the set, send its final snapshot with `isFinal: true`. For `squat`:

- `insufficient_data`: stable standing has not been established (or tracking was lost before
  any completed rep). Count is null. This includes the empty batch and tiny two-frame example.
- `partial`: observations establish readiness or completed reps. Count is the number of
  observed completed cycles, including zero when ready with none completed.
- `complete`: final snapshot ends in confirmed standing with no unavailable angles or tracking
  breaks anywhere in the received sequence. This does not imply form scores are available.
- Final snapshots with tracking loss or a confirmed unfinished rep remain `partial`. Read the
  limitations; the set need not still be recording. Completed reps survive tracking loss.

Only completed reps appear in `reps`; finalization never finishes a rep automatically.
There is no server session state. No hint or another registered hint returns `not_implemented`.

`source.durationMs` is the last sample timestamp, or null if the batch
is empty. It reports received sample coverage, not measured exercise duration. For live
analysis, playback is relative to the same zero point. Local video recording for replay is future work.

HTTP 200 body is a full `AnalysisResponse`. User-selected exercise confidence, all scores,
camera quality score/fullBodyVisible, and scoring metadata remain null. The six-rep fixture
is never substituted for a request. Empty issues do not establish good form.

`cameraQuality.issues` also describes sampled-frame tracking coverage and named missing,
outside-image, unknown/low-visibility joints. Coverage refers to the whole received sequence,
not elapsed time or current readiness. Push-ups include shoulder/hip/ankle visibility
coverage on the locked side, without assessing alignment or gating elbow counts on those
extra joints. These strings are display text, not machine-readable metrics or severity
codes. Do not parse them or treat the array length as an error count. See
[tracking feedback](../apps/api/TRACKING_FEEDBACK.md). Response shape remains unchanged.

**Squat measurement policy:** choose the first usable hip-knee-ankle side, preferring left
if both work in that frame, and keep it for the entire set. Each joint needs visibility at
least 0.7 and in-frame coordinates; undefined geometry is unavailable. Missing angles or gaps
over 300 ms reset readiness and discard unfinished reps. Start with stable standing in a side
view. Camera orientation is not automatically validated. See apps/api/README.md for thresholds.

Per-rep `measurements` contains `durationMs` and either `minSmoothedLeftKneeAngleDeg` or
`minSmoothedRightKneeAngleDeg`. The minimum uses a causal three-sample median after descent
confirmation, not raw samples. Its `minimum_knee_angle` key moment has a readable label.
The timeline includes rep start, minimum-angle moment, and rep end. Timestamps include
smoothing/confirmation latency. No front-view knee-tracking finding is inferred from this.

For this analyzer, `provenance.kind: "measured"` identifies computation from the supplied
poses; it does not attest that the client captured them from a camera. Keep synthetic inputs
clearly labeled in demos/tests. Counting heuristics are not a validated fitness assessment.

**Push-up support:** select `exerciseHint: "push-up"`. The same status, replay, visibility,
side-locking and finalization policies apply, using a top/return zone instead of standing.
The triplet is shoulder-elbow-wrist. Counter v2 uses top >=150 and bottom <=100 degrees,
60 ms of consecutive raw observations plus current median confirmation, and overlapping
phase evidence. Squat's old sequential confirmation is unchanged. Start is the first raw
descent-zone observation in the confirmed run. Reanalysis changes earlier timestamps and
measurements; the wire shape is unchanged. See [counting policy](../apps/api/COUNTING.md).
Results use `minSmoothedLeftElbowAngleDeg` or
`minSmoothedRightElbowAngleDeg`, plus `durationMs` and a `minimum_elbow_angle` key moment.
Additional push-up `measurements` keys (the dictionary is extensible; old results may lack them):

| Key | Meaning |
| --- | --- |
| `maxSmoothedLeftElbowAngleDeg` / `maxSmoothedRightElbowAngleDeg` | Maximum on the selected side over the same window as the existing minimum |
| `smoothedLeftElbowExcursionDeg` / `smoothedRightElbowExcursionDeg` | That maximum minus minimum, in degrees |
| `angleMeasurementStartMs` | Inclusive timestamp of descent confirmation; extrema cover this through `endMs` |
| `timeToMinElbowAngleMs` | Existing minimum key-moment timestamp minus `startMs` |
| `timeFromMinElbowAngleMs` | `endMs` minus the minimum key-moment timestamp |

The two time parts sum to `durationMs`; they include pauses and confirmation delay, not
isolated lowering/lifting durations. Extrema exclude the initial top position before descent
confirmation and later samples after rep completion. They describe observed 2D excursion,
not a range-of-motion score. All `metrics` score fields remain null. See
[measurement definitions](../apps/api/MEASUREMENTS.md) and the explicitly synthetic
`contracts/examples/pushup-analysis.json` example. Missing keys mean unavailable, never zero.
No body-alignment, depth-quality, or injury claim is implied by these provisional cycles.

**Descriptive push-up body-line angle:** completed reps additionally include
`medianLeftShoulderHipAnkleAngleDeg` or `medianRightShoulderHipAnkleAngleDeg`, plus
`bodyLineSampleCount` and `bodyLineUsableSampleCount`. The median uses raw, aspect-corrected
2D angles at the hip over the inclusive counted rep interval. It requires both boundaries,
at least three samples, every angle usable, and no sample gap over 300 ms; otherwise null.
The selected side matches elbow counting. These keys are additive in the existing numeric
dictionary; old results may omit them. Neither a quality score nor a sag/pike classification
is implied. Body-line failure does not remove counted reps. See [BODY_LINE.md](../apps/api/BODY_LINE.md)
for exact semantics, limits, and the reviewed real-clip values.

**Push-up comparison flags:** from rep 3 onward, compare with the immediately preceding two
completed reps. Require continuous usable angles across that entire reference/current span,
including between reps. Timing policy v2 compares with each prior duration independently;
excursion references must differ by at most 10°. Eligible comparisons emit numeric evidence even without a flag.

- `PUSHUP_REP_DURATION_CHANGED` (timing v2): current duration is longer than BOTH preceding
  durations by at least max(500 ms, 30% of each reference), or shorter than BOTH by those
  margins. This replaces the original 20% reference-spread eligibility gate; no count/angle change.
- `PUSHUP_ELBOW_EXCURSION_REDUCED`: excursion reduction >= max(15°, 20% of reference median).

These are uncalibrated review heuristics. Issue severity is `low`, confidence is null,
explanations contain measured values/reference reps/thresholds, and IDs link rep/session
issues to timeline events at the current rep start. No bad-form, fatigue, or injury inference.
`summary.primaryFocus` becomes `rep_consistency_review` when flags exist; scores remain null.
Earlier rep results never change when frames are appended, including later tracking loss.

New optional measurement keys: `comparisonReferenceStartRep`, `comparisonReferenceEndRep`,
`referenceMedianDurationMs`, `durationDeltaMs`, `durationDeltaPercent`, `durationChangeThresholdMs`,
`durationComparisonVersion` (2), `referenceMinDurationMs`, `referenceMaxDurationMs`,
`durationReviewLowerBoundMs`, `durationReviewUpperBoundMs`,
`referenceMedianElbowExcursionDeg`, `elbowExcursionDeltaDeg`, `elbowExcursionDeltaPercent`,
`elbowExcursionReductionThresholdDeg`. Deltas are current minus reference. Missing keys mean
unavailable (too few reps, tracking loss, invalid duration or unstable/missing range reference),
not zero change. Existing `limitations` gives rep-specific unavailability reasons.
Timing bounds are current-duration boundaries, not delta values or desired tempo. The lower
bound can be negative, making shorter flags impossible for positive durations. In v2,
`durationChangeThresholdMs` is the distance from the median to the bound in the current delta's
direction (upper for zero/positive delta); older results without the version key use the original
median margin. Clients should render supplied flags/explanations and support absent optional keys.
See [comparison policy](../apps/api/COMPARISONS.md) for exact units and limitations and
`contracts/examples/pushup-comparison-analysis.json` for a clearly synthetic flagged example.
The user-selected push-up demo replaces the earlier squat demo priority; wire shapes are unchanged.

Registered IDs: `squat`, `push-up`, `lunge`, `barbell-squat`, `bicep-curl`, `shoulder-press`,
`deadlift`. Unknown hints return HTTP 400 `UNKNOWN_EXERCISE`. Registration is not an assertion
of implementation. No automatic recognition exists yet.

From the repository root with the API running:

```bash
curl -s http://localhost:8000/api/v1/live/analyze-batch \
  -H 'Content-Type: application/json' \
  --data-binary @contracts/examples/live-pose-batch.json
```

## POST /api/v1/videos/analyze

Content-Type: `multipart/form-data`, with required `file` and optional text `exerciseHint`.
Let the browser set multipart headers; the client already does this. No JSON wrapper.

**Implemented local upload behavior:** HTTP 200 returns the existing `AnalysisResponse`,
with `source.type: "upload"`, a server-generated session ID, and timestamps relative to the
upright decoded clip. `durationMs` covers the last decoded frame (not necessarily the media
container's nominal duration). Counting uses the same analyzer as live. Scores remain null.

Send `exerciseHint: "push-up"` for the demo. The multipart field remains optional in the wire
shape, but real processing requires explicit selection: missing/empty returns 400
`EXERCISE_REQUIRED`; unknown IDs return `UNKNOWN_EXERCISE`; registered but unimplemented
IDs return `EXERCISE_NOT_SUPPORTED`. Legacy `squat` also counts. No automatic detection.

Accepted: nonempty MP4/MOV/WebM, <=250 MiB, <=120 seconds, <=4K pixels and <=4096 per axis,
fixed upright square-pixel dimensions, valid monotonic source timestamps. HEVC MOV works
on Computer A; H.264 MP4 is a fallback for decoder/browser compatibility. MIME headers do
not establish validity. Processing needs the optional local packages/model in VIDEO_SETUP.md.

Uploads are synchronous, run in a worker thread, and permit one native extraction per API
process. Concurrent analysis returns 503 `VIDEO_PROCESSOR_BUSY`. Temporary copies and
multipart files are closed/removed when processing exits; the result contains no video URL
or pose-frame sequence. Keep the original browser file for playback. Aborting a browser
request does not immediately cancel native processing. No queue or persisted job exists.

The 180-second extraction deadline is cooperative between native calls, not a hard native
execution timeout. Starlette spools multipart data before handler size/concurrency checks;
these are local-demo processing limits, not a hard incoming body/disk quota. Run one worker.

Application errors retain the existing `detail.code` / `detail.message` shape:

| HTTP | Codes |
| --- | --- |
| 400 | `EXERCISE_REQUIRED`, `UNKNOWN_EXERCISE`, `EXERCISE_NOT_SUPPORTED`, `EMPTY_VIDEO`, `INVALID_VIDEO` |
| 413 | `VIDEO_TOO_LARGE` |
| 415 | `UNSUPPORTED_VIDEO_TYPE` |
| 503 | `VIDEO_SETUP_REQUIRED`, `VIDEO_PROCESSOR_BUSY` |
| 504 | `VIDEO_PROCESSING_TIMEOUT` |
| 500 | `VIDEO_PROCESSING_FAILED` (sanitized message; details in backend terminal) |

Missing/malformed multipart fields use FastAPI's existing HTTP 422 shape. Insufficient pose
evidence returns HTTP 200 with honest `insufficient_data`/`partial` analysis, never mock data.
See [HTTP upload guide](../apps/api/HTTP_UPLOAD.md) for exact curl commands and B's checklist.
**Frontend behavior:** the integrated client uses a separate 240-second upload timeout.
Health/live/coach requests retain 15 seconds.

## AnalysisResponse

### Additive video playback endpoint

`POST /api/v1/videos/analyze-with-pose` accepts the same multipart fields, limits, and
errors as `/videos/analyze`. It returns `VideoAnalysisResponse`:

```typescript
{
  contractVersion: "1.0";
  analysis: AnalysisResponse;
  poseTrack: {
    imageWidth: number;
    imageHeight: number;
    durationMs: number;
    frames: PoseFrame[];
  };
}
```

This addition supplies the joints needed for video overlays without changing the existing
analysis endpoint or making clients extract poses twice. One upload/extraction feeds both
analysis and playback. The browser keeps the original selected file; no video URL or server
storage is added. Track duration matches analysis source duration. Dimensions are the upright,
unmirrored, square-pixel image after rotation; at most 4096 per axis and 4K total area.
At most 1800 sampled frames / 120 seconds. Frame indices/timestamps strictly increase.
Empty-landmark frames preserve no-pose/multiple-person gaps. All frames use the canonical
coordinates above, including unmodified offscreen estimates. Nothing is interpolated.

Render joints only with visibility >=0.7 and in-frame x/y, and connections only when both
endpoints qualify. Fit to the **contained image rectangle**, including letterbox offsets.
Playback uses the most recent sample at/before `video.currentTime * 1000`, hiding samples
older than 150 ms, during seeks, or when image aspect ratios disagree. This tolerance is a
rendering policy, not calibrated tracking accuracy. Skeletons are raw pose observations;
rep measurements use causal smoothing and can differ slightly. Colour denotes tracking,
not good/bad form. Native fullscreen/Picture-in-Picture shows the video without the sibling
canvas; use inline playback for the overlay.

Example: `contracts/examples/pushup-video-with-pose.json` is clearly **synthetic**, with no
matching video. The UI must not overlay it on a user's unrelated recording. Details and
browser setup: [POSE_OVERLAY.md](POSE_OVERLAY.md).

## Analysis response fields

Read the complete six-rep JSON fixture and generated schema for exact fields. Key semantics:

| Field | Meaning |
| --- | --- |
| `status`, `provenance` | Capability/result state and measured/synthetic/placeholder labeling |
| `source` | `live` or `upload`; nullable duration in milliseconds |
| `exercise` | Nullable selection/classification; confidence null for a user hint |
| `cameraQuality` | Nullable score and fullBodyVisible, plus readable issues |
| `summary` | Nullable overallScore, totalReps, primaryFocus; readable headline |
| `metrics` | Nullable ROM, symmetry, tempo, stability, consistency scores |
| `reps` | Completed reps in order, numbered from 1; non-overlapping intervals |
| `measurements` per rep | Named numeric/null measurements with units in keys, e.g. `minLeftKneeAngleDeg` |
| `issues` per rep | Full issue objects matching those in the session issue list by unique `id` |
| `keyMoments` per rep | In-rep timestamps and extensible type/label, e.g. `bottom_position` |
| `issues` per session | Unique IDs, code, severity, nullable confidence, cue, explanation, interval, joints |
| `timeline` | Chronological `rep_start`, `rep_end`, `key_moment`, or `issue` events |
| `limitations` | Honest reasons for missing/uncertain results |
| `scoring` | Nullable version, method, and metric weights; see SCORING.md |

Issue severity is a coaching priority, **not** an injury risk assessment. Time intervals
use start/end milliseconds. All events must fit within known source duration. `totalReps`
equals `reps.length` when known; unknown analysis uses null, not zero. Issue IDs tie timeline
events to issue cards. Timeline `repNumber` and `issueId` are nullable when not applicable.
New issue codes, measurement keys, and key-moment types are extensible strings: frontend
should display the supplied label/cue and gracefully handle unfamiliar ones.

Derive worst rep from the lowest non-null `rep.score`; ties choose the earliest. If all
scores are null, there is no known worst rep. Seek to `rep.startMs / 1000` in a video player.
Never seek into an unrelated uploaded video using the synthetic fixture's timestamps.

## POST /api/v1/coach

```typescript
type CoachRequest = {
  analysis: AnalysisResponse;
  mode: "summary" | "next_set" | "qa";
  question?: string | null; // required, nonblank for qa; max 1000 characters
  responseStyle?: "evidence" | "conversation"; // default evidence
  history?: { role: "user" | "assistant"; content: string }[]; // max 12, 1–2000 chars each
};
```

HTTP 200: `contractVersion`, `sessionId`, `mode`, `provider: "fallback" | "openai"`,
`message`, `evidence` (dot paths into the analysis), and `limitations`.
Default `fallback` makes no network call. It summarizes supplied counts, push-up timing,
observed elbow excursion/comparisons, or the legacy supplied score. Synthetic data stays
labeled and unknown scores stay unknown. Local free-form QA is unsupported.
Optional `COACH_PROVIDER=openai` plus a backend key and SDK enables bounded evidence
selection; the backend renders reviewed wording. Provider failures fall back honestly.
`evidence` uses zero-based array dot paths; display `limitations` alongside `message`.
Conversation style is an additive request extension: the model writes short replies using
reviewed evidence plus bounded history. Recognized count disputes use local guidance;
unknown causes must not become invented explanations. The response shape stays unchanged.
The server stores no conversation; the caller supplies recent messages on each request.
The current UI uses conversation style, shows short replies and keeps evidence/limitations
in expandable details. Omitted fields retain legacy behavior. **Update backend and frontend
together:** older strict validators reject these new fields with 422.
See AI_COACH.md, `contracts/examples/coach-conversation-request.json`, and apps/api/COACH_SETUP.md.

## Errors and frontend behavior

- HTTP 400: application error `{"detail":{"code":"...","message":"..."}}`.
- HTTP 422: FastAPI validation shape `{"detail":[{"loc":[...],"msg":"...","type":"...",...}]}`.
  Client shows a friendly message; developers inspect the network response for field errors.
- Upload-specific statuses and codes are listed above; all use the application error shape.
- Network/unexpected server errors: client throws `ApiError`; no mock substitution.
- Client timeout is 15 seconds for short requests and 240 seconds for uploads. Never automatically retry a timed-out upload.
- No auth or durable session storage exists. Health does not expose secrets/settings.

Change procedure and regeneration commands are in `contracts/README.md` and AGENTS.md.
