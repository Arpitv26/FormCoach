# Recorded push-up validation — September 26, 2026

## Result

All four supplied recordings decode on Computer A without conversion. They are HEVC
videos in MOV containers, roughly 60 fps. The portrait clip's rotation metadata is applied
before pose extraction. Google's pretrained MediaPipe Pose Landmarker Full produced the
poses; our existing Python elbow-cycle analyzer produced the counts.

| Local file | Duration (approx.) | Size | Upright dimensions | Human count | Before fix | After fix |
| --- | --- | --- | --- | --- | --- | --- |
| `IMG_6937.MOV` | 19.11 s | 121.7 MiB | 3840 × 2160 | 3 | 3 | 3 |
| `IMG_6938.MOV` | 3.52 s | 22.2 MiB | 2160 × 3840 | 1 | 0 | 1 |
| `IMG_6939.MOV` | 3.07 s | 19.7 MiB | 3840 × 2160 | 1 | 1 | 1 |
| `IMG_6940.MOV` | 6.94 s | 44.1 MiB | 3840 × 2160 | 2 | 2 | 2 |

The participant supplied the human counts. Visual review of frame sequences at 0.25–0.35 s
spacing also matched these seven cycles. These are development clips, including one used
to find a bug; this is not an independent accuracy benchmark or proof of generalization.

All four final responses are `complete`. Cumulative replay through the actual HTTP live
endpoint matched the counts, preserved completed reps across batches, and returned an
identical response when the final request was repeated. Counts passed for both the left
elbow (6937–6939) and right elbow (6940), selected by the existing visibility rules.

## Timing fix

The short portrait clip initially returned zero completed reps. At 3268 ms, one observation
both confirmed ascent and met the straight-arm threshold. The old counter discarded that
observation for the next phase, delaying the top-position confirmation timer by one sample.
The recording ended before that unnecessarily delayed timer completed.

The shared counter now starts the next phase's timer on the transition observation when
that observation meets its threshold. It still requires the full 150 ms confirmation;
angle thresholds, smoothing, and finalization rules are unchanged. Synthetic regression
tests cover completion at the boundary, insufficient dwell, and a brief extension spike.
The fix was checked against the cached real poses from all four clips and the existing
squat tests. No clip names or special-case thresholds appear in the algorithm.
The complete backend suite passes **213 tests**; Ruff lint/format and schema checks pass.

Observed rep intervals after the fix (seconds from the start of each clip):

| Clip | Rep intervals |
| --- | --- |
| 6937 | 4.402–6.937; 13.607–15.540; 16.475–18.808 |
| 6938 | 1.467–3.468 |
| 6939 | 0.733–2.735 |
| 6940 | 1.467–3.468; 4.202–6.270 |

These boundaries come from smoothed angles and phase confirmation. They include latency;
visual sequence review establishes correspondence to the observed cycles, not millisecond
accuracy against manually annotated start/end times. Verify seeking again in the actual UI.

## Repeat on Computer A

The four original MOV files are in the repository root and ignored by Git. Follow
[VIDEO_SETUP.md](VIDEO_SETUP.md) once to install optional packages and download the model.
From the repository root, run:

```bash
cd apps/api
source .venv/bin/activate
python -m app.tools.analyze_video ../../IMG_6937.MOV --output artifacts/check-6937
python -m app.tools.analyze_video ../../IMG_6938.MOV --output artifacts/check-6938
python -m app.tools.analyze_video ../../IMG_6939.MOV --output artifacts/check-6939
python -m app.tools.analyze_video ../../IMG_6940.MOV --output artifacts/check-6940
```

Expect counts **3, 1, 1, 2** and `complete`. Use new output folder names if those folders
already exist; the tool refuses to overwrite a previous result. Each run writes `poses.json`
and `analysis.json`. No API server is needed for extraction.

For HTTP verification, open a second terminal at the repository root:

```bash
cd apps/api
source .venv/bin/activate
python -m uvicorn app.main:app --port 8000
```

Leave it running. In the first terminal, still in `apps/api`, run:

```bash
python -m app.tools.replay_live artifacts/check-6937/poses.json --expected-reps 3
python -m app.tools.replay_live artifacts/check-6938/poses.json --expected-reps 1
python -m app.tools.replay_live artifacts/check-6939/poses.json --expected-reps 1
python -m app.tools.replay_live artifacts/check-6940/poses.json --expected-reps 2
```

Each report should say `count_match`. Stop the server with **Control+C** in its terminal.
Another computer must obtain the consented clips separately; recordings are not in Git.

## Local evidence and remaining limits

Computer A's ignored `artifacts/recording-review/` contains metadata, visual frame sheets,
`recording-analysis.png` (angle/timing chart), original model outputs under `baseline/`,
and fixed-counter results plus HTTP replay reports under `reviewed/`. Cached poses were
reused after the counter fix because pose extraction did not change. Do not commit these
files or turn the recordings into public test fixtures.

- This validates counting on these clips only. Scores remain null; body alignment, form
  issues, symmetry, and injury-related conclusions are not implemented or validated.
- The camera angle is not automatically classified. A selected `push-up` hint is not
  exercise recognition. A successful count is not a judgment of correct form.
- 6939 is a short landscape smoke test; 6937 provides three reps and pauses, while 6940
  checks the opposite visible side. Keep 6938 as the short portrait boundary regression.
- Processing the 4K clips took tens of seconds with other review work running. This was
  not a controlled speed benchmark. Measure response time and coordinate the frontend's
  request timeout/loading state before enabling synchronous HTTP uploads.
- HTTP upload integration is now implemented and tested; see the follow-up below.
  Next check Computer B's playback against these same timestamps.

## Follow-up: actual HTTP video uploads

The real MOV bytes were sent as multipart requests to a running local Uvicorn server,
with `exerciseHint=push-up`. Each request ran fresh MediaPipe extraction and returned the
existing measured `AnalysisResponse`; these were not cached pose replays.

| Clip | HTTP | Expected / returned count | Status | Wall time on Computer A |
| --- | --- | --- | --- | --- |
| 6939 | 200 | 1 / 1 | complete | 8.82 s |
| 6938 | 200 | 1 / 1 | complete | 10.51 s |
| 6940 | 200 | 2 / 2 | complete | 13.08 s |
| 6937 | 200 | 3 / 3 | complete | 39.06 s |

Health checks during those uploads returned in 23–93 ms. A corrupt MOV returned HTTP 400
`INVALID_VIDEO`. These are single runs on this Mac, not latency guarantees. The longest
clip exceeds the frontend's existing 15-second timeout; Computer B must set a separate
240-second upload timeout before integration. See [HTTP_UPLOAD.md](HTTP_UPLOAD.md).

The backend suite now passes **234 tests**, including upload cleanup after success/failure,
size/type/selection errors, unavailable setup, sanitized internal errors, concurrent busy
handling, health responsiveness, and preservation of real-analysis unknowns. Native inference
is tested separately with the local recordings, so CI needs no model/video download.
Local HTTP responses/timings are ignored under `artifacts/upload-check/`.

## Follow-up: descriptive measurements on saved real poses

The measurement checkpoint replays the four saved captures through HTTP route handling
(TestClient), including cumulative and repeated-final checks. Counts remain 3/1/1/2;
all seven start/end times and minimum-angle moments match the prior real-upload responses.
An independent causal-median calculation reproduces each maximum, minimum, and excursion
within the reported angle window. No new native extraction was needed for this math change.

| Clip / rep | Counted time | Time to minimum | Time after minimum | Observed elbow excursion |
| --- | --- | --- | --- | --- |
| 6937 / 1 | 2535 ms | 1268 ms | 1267 ms | 102.5° |
| 6937 / 2 | 1933 ms | 866 ms | 1067 ms | 105.6° |
| 6937 / 3 | 2333 ms | 1133 ms | 1200 ms | 101.4° |
| 6938 / 1 | 2001 ms | 801 ms | 1200 ms | 107.8° |
| 6939 / 1 | 2002 ms | 1000 ms | 1002 ms | 104.8° |
| 6940 / 1 | 2001 ms | 1001 ms | 1000 ms | 100.4° |
| 6940 / 2 | 2068 ms | 1200 ms | 868 ms | 102.0° |

These are descriptive 2D observations, not quality rankings across angles or calibrated
anatomical motion. See MEASUREMENTS.md for the window and timing limitations.
Backend suite: **242 tests pass**. Local replay evidence: `artifacts/measurement-check/`.

## Follow-up: within-set comparison rules

The four saved real pose captures were replayed through route handling with cumulative and
repeated-final checks. Counts, rep boundaries, and past rep results remain unchanged.
**No flags were produced.** The one/two-rep clips lack two prior references. In 6937, rep 3's
reference elbow excursion is 104.022°, its change is -2.604° (-2.503%), and the configured
reduction threshold is 20.804°: no range flag. The duration reference is ineligible because
2535 ms and 1933 ms differ by approximately 26.9% of their 2234 ms median (limit 20%).

This is evidence of correct arithmetic and conservative behavior on these clips, not proof
of form quality or positive-case detection accuracy. Positive duration/range flags are tested
with authored geometry and the explicitly synthetic three-rep fixture. A separate real
positive example still needs video review. Thresholds were not fitted to force a demo flag.
Local reports: `artifacts/comparison-check/`. Policy: COMPARISONS.md.

Comparison checkpoint: **263 backend tests pass**; lint, formatting, Python schema checks,
and frontend generated-type checks pass. No new runtime dependencies or schema fields.

## Follow-up: current backend rehearsal (code `4b87e35`)

Fresh native MediaPipe extraction was run through multipart `/videos/analyze-with-pose`
route handling with FastAPI TestClient, then each returned analysis was sent to `/coach`
in `next_set` mode. This exercised actual video bytes and the current tracking/body-line
features, rather than reusing cached poses. It did not exercise a network socket or browser.
The coach was explicitly local; no paid API request or credential change was made.

| Clip | HTTP | Reps | Status | Wall time, one run |
| --- | --- | --- | --- | --- |
| 6939 | 200 | 1 | complete | 7.15 s |
| 6938 (portrait) | 200 | 1 | complete | 9.79 s |
| 6940 | 200 | 2 | complete | 14.59 s |
| 6937 | 200 | 3 | complete | 41.56 s |
| Generated blank video | 200 | null | insufficient_data | 0.37 s |

- All returned pose tracks reproduced the exact rep measurements, timeline and summary when
  passed back through the analyzer. Portrait dimensions were 2160 × 3840; others 3840 × 2160.
- Each real result supplied descriptive body-line coaching with resolvable evidence paths.
  All scores remained null and the real clips retained zero comparison flags.
- The blank clip had 15 empty-landmark frames, no reps and no invented body-line finding.
  This is an artificial no-person input, not a real occlusion benchmark.
- A corrupt MOV returned `400 INVALID_VIDEO`; subsequent real uploads succeeded in the
  same app instance. Health requests during extraction all succeeded, with maximum observed
  time 65.69 ms. These single local runs are not performance guarantees.
- MediaPipe's macOS graphics initialization aborted in the restricted tool sandbox. The
  approved rerun outside that sandbox passed. The user's existing servers were left running.

Private script, responses and timing summary are ignored under `artifacts/backend-rehearsal/`.
The latest unit suite remains **375 passing tests** (previous code checkpoint); this rehearsal
required no runtime change. Real positive comparison validation and B's complete browser flow
remain pending. The human confirmed the gym trip/recording and frontend PR are not ready yet;
remote `frontend` still points to `5dd6bb4` at this check.
