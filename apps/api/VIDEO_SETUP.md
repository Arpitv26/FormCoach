# Prerecorded push-up video — local backend checkpoint

**Current scope:** a local command extracts poses from a video and writes measured analysis.
The HTTP upload route still returns 501; connect it only after we validate the actual clip.
The frontend camera is not required. No API key or cloud upload is used by this command.

We use Google's pretrained [MediaPipe Pose Landmarker](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/python)
to estimate body landmarks. Our Python code counts elbow cycles from those landmarks.
The model does not decide our rep count or generate form advice. Camera/model accuracy and
counting thresholds still require comparison with real push-up footage.

## One-time setup on Computer A

The optional packages have been pinned for Python 3.12 on Apple Silicon. The ordinary API
setup stays small and does not install them. From the repository folder containing `apps/`:

```bash
cd apps/api
source .venv/bin/activate
python -m pip install -r requirements-cv.txt
python -m pip check
mkdir -p artifacts/models artifacts/captures
curl --fail --location --output artifacts/models/pose_landmarker_full.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task
shasum -a 256 artifacts/models/pose_landmarker_full.task
```

`pip check` should say **No broken requirements found**. The model is roughly 9 MiB;
its SHA-256 should be:

```text
5134a3aad27a58b93da0088d431f366da362b44e3ccfbe3462b3827a839011b1
```

If `.venv` is missing, first follow [README.md](README.md). Only one OpenCV distribution
belongs in this environment: `opencv-contrib-python`, required by the pinned MediaPipe
package. Do not additionally install `opencv-python` or a headless variant into it.
If another Mac cannot install these optional wheels, keep its basic API setup and run video
extraction on Computer A while resolving platform compatibility separately.

## Analyze your recording

Still in `apps/api`, open the ignored capture folder:

```bash
open artifacts/captures
```

Copy the recording there using Finder. Name it `pushups.mp4` **only if it is already an MP4**;
keep `.mov` for a MOV. Renaming an extension does not convert a video. Then run:

```bash
python -m app.tools.analyze_video artifacts/captures/pushups.mp4 --output artifacts/pushup-run-1
```

For a MOV, replace the input with `artifacts/captures/pushups.mov`. Paths containing spaces
must go inside quotes. A server does not need to be running. This may take a minute; model
startup can print library diagnostic messages. Success prints a status, observed rep count
(or `unknown`), and the output folder. Exit code 0 means files were written, **not** that the
count is accurate. File/setup/processing failures exit with code 2.

The output folder contains:

- `poses.json`: normalized poses and original clip-relative timestamps in the existing
  `LiveBatchRequest` shape, ready for the replay checker. No SDK-specific objects.
- `analysis.json`: existing v1.0 response with `source.type: "upload"`, observed completed
  reps, elbow-angle measurements, timestamps, and limitations. Scores are still null.

Choose a new output folder for each attempt, e.g. `artifacts/pushup-run-2`. The command
refuses to overwrite a previous run. Both videos and output files stay on this computer.
Everything under `artifacts/` is already ignored by Git.

## Compare the result with what happened

Manually count completed push-ups in the recording. Inspect `analysis.json` and compare
each rep's `startMs`, `endMs`, and key moment with the video (divide milliseconds by 1000).
Keep track of any missed/extra reps and timing differences. Smoothing introduces latency.

To check the saved poses through the actual HTTP API too, start Uvicorn in a separate
terminal as described in [examples/README.md](examples/README.md), then run:

```bash
python -m app.tools.replay_live artifacts/pushup-run-1/poses.json --expected-reps 3 > artifacts/pushup-run-1/replay-report.json
cat artifacts/pushup-run-1/replay-report.json
```

Replace `3` with the number you actually counted. Replay's analysis is labeled `live` because
it exercises that endpoint; it uses the same recorded poses, not a new camera capture.
It checks stable cumulative responses and identical final replay. The local upload analysis
and replay may differ in source duration: upload covers the last decoded frame, while the
live contract reports the last sampled pose timestamp. Rep timestamps share the same clock.

## Initial limits and failures

- Local MP4/MOV/WebM files only, at most 250 MiB and 120 seconds; start with a short clip.
  H.264 MP4 is the preferred fallback if the decoder rejects a codec.
- Up to 4K pixels, at most 4096 on either axis, fixed dimensions, square pixels. Export at
  1080p when troubleshooting. Stream rotation metadata is applied before inference.
- Samples the first observed frame in each 1/15-second interval, at most 1800 sampled
  frames. No interpolation. Source-frame indices and timestamps are preserved.
- Reads decoded timestamps via OpenCV, including variable frame rate. Missing/reversed
  timestamps fail explicitly; there is no fallback to frame index divided by assumed fps.
- Up to 30000 decoded source frames. A 180-second processing guard is checked between
  calls; native decoder/inference calls can block. This is a local tool, not a hardened
  public upload service. Open/read timeouts are also requested from the FFmpeg decoder.
- No detected person or multiple detected people yields empty landmarks, causing honest
  tracking gaps. A model can still miss another person; film one participant only.
- Shoulder, elbow, and wrist must remain visible for counting. Include hip and ankle for
  later body-line measurements. This version does not assess body alignment or correct form.
- Keep a straight-arm top pause before/after the set. Missing or low-visibility frames
  discard an unfinished rep. Shallow attempts may not meet the provisional flexion threshold.
- macOS sandboxed agents may need permission to run MediaPipe's graphics initialization
  outside the sandbox. Ordinary Terminal execution uses the normal desktop environment.

Sources: [MediaPipe model bundles](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/index)
and [OpenCV timestamp/rotation properties](https://docs.opencv.org/4.13.0/d4/d15/group__videoio__flags__base.html).
Real-footage validation remains pending until the user's recording is analyzed and reviewed.
