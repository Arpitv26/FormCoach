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
- No real exercise analysis is supported in bootstrap. Profiles describe planned capability.
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
indices/timestamps and must be handled by future analysis, never filled with invented poses.

When the user ends the set, send its final snapshot with `isFinal: true`. Future analyzers
return `partial` while the set is open and `complete` when finalized with enough evidence.
Only completed reps appear in `reps`; an unfinished repetition is not counted. Missing data
may produce `insufficient_data`. Bootstrap always returns `not_implemented`, including for
an empty batch or final snapshot. It stores no session state and computes no movement.

`source.durationMs` in the placeholder is the last sample timestamp, or null if the batch
is empty. It reports received sample coverage, not measured exercise duration. For live
analysis, playback is relative to the same zero point. Local video recording for replay is future work.

HTTP 200 body is a full `AnalysisResponse`. The placeholder echoes the session and known
hint (confidence null), and returns null scores, null totalReps, empty reps/issues/timeline,
and a clear limitation. The sample six-rep fixture is never returned for an arbitrary request.

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

**Bootstrap behavior:** HTTP 501, no pose extraction, no saved video, no fabricated analysis:

```json
{
  "detail": {
    "code": "VIDEO_ANALYSIS_NOT_IMPLEMENTED",
    "message": "Video pose extraction is not implemented in this bootstrap."
  }
}
```

The declared future HTTP 200 body is `AnalysisResponse`, with `source.type: "upload"`,
actual clip duration, and timestamps relative to the upright decoded clip. The backend
will generate the upload session ID. Video acceptance limits and codec handling must be
defined before enabling real extraction; the bootstrap is a local development endpoint.
Do not upload large recordings just to test this stub. Starlette may spool multipart data
to a temporary file before the handler closes it; this is not persistent video storage.

## AnalysisResponse

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
};
```

HTTP 200: `contractVersion`, `sessionId`, `mode`, `provider: "fallback" | "openai"`,
`message`, `evidence` (dot paths into the analysis), and `limitations`.
The bootstrap always uses `fallback`, makes no network call, states that data is synthetic
when applicable, quotes the supplied score only when available, and admits that free-form
QA is not implemented. It does not echo arbitrary issue/cue text as advice. API keys do
not enable unfinished functionality. The future adapter must follow AI_COACH.md.

## Errors and frontend behavior

- HTTP 400: application error `{"detail":{"code":"...","message":"..."}}`.
- HTTP 422: FastAPI validation shape `{"detail":[{"loc":[...],"msg":"...","type":"...",...}]}`.
  Client shows a friendly message; developers inspect the network response for field errors.
- HTTP 501: explicit unimplemented video processing (same shape as 400).
- Network/unexpected server errors: client throws `ApiError`; no mock substitution.
- Client timeout is 15 seconds; future real video extraction may require a deliberate increase.
- No auth or durable session storage exists. Health does not expose secrets/settings.

Change procedure and regeneration commands are in `contracts/README.md` and AGENTS.md.
