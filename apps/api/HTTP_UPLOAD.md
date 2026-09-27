# Real video uploads — Computer A and Computer B

`POST /api/v1/videos/analyze` now runs the local MediaPipe adapter and the same movement
analyzer as live batches. The request and response shapes stay at contract version **1.0**.
This is a synchronous local demo endpoint: one request waits for one analysis result.

**Current integration:** the frontend already uses the 240-second timeout and the additive
`/videos/analyze-with-pose` endpoint for skeleton playback. The analysis-only endpoint below
remains supported. See ../../docs/POSE_OVERLAY.md and ../../docs/NEXT_STEPS.md.

## Try it on Computer A

The optional packages and model must be installed once using [VIDEO_SETUP.md](VIDEO_SETUP.md).
They are already installed on the original Computer A. No OpenAI key is needed.

Open a terminal at the repository root (the folder containing `apps/`), then run:

```bash
cd apps/api
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Success says `Uvicorn running on http://127.0.0.1:8000`. Leave this terminal running.
Use one worker for this demo; the processing limit is per process. If port 8000 is busy,
use `--port 8001` and change the URL below to match. Stop with **Control+C**.

Open a second terminal at the repository root and run:

```bash
mkdir -p apps/api/artifacts/upload-demo
curl --fail-with-body --max-time 240 \
  -F 'file=@IMG_6939.MOV' \
  -F 'exerciseHint=push-up' \
  http://127.0.0.1:8000/api/v1/videos/analyze \
  -o apps/api/artifacts/upload-demo/analysis.json
apps/api/.venv/bin/python -m json.tool apps/api/artifacts/upload-demo/analysis.json
```

`curl` sends the local video to the API on this same computer. Wait for it to finish.
The second command prints the saved JSON clearly. For the supplied 6939 recording, expect
HTTP success, `source.type: "upload"`, `status: "complete"`, and `summary.totalReps: 1`.
Scores remain null. The report stays in an ignored folder. Replace the filename for another
clip; the known counts are 6937=3, 6938=1, 6939=1, 6940=2.

Alternatively open http://127.0.0.1:8000/docs, expand **POST /api/v1/videos/analyze**, click
**Try it out**, choose the video, enter `push-up` for `exerciseHint`, and click **Execute**.
A new session ID is created for every successful upload; no result is saved on the server.

## Frontend handoff

Computer B owns the client/UI changes. Read docs/API_CONTRACT.md and retain the existing
`AnalysisResponse` types. No generated type changes are required for this checkpoint.

- Send multipart fields `file` and `exerciseHint: "push-up"`. Browser `FormData` sets the
  Content-Type boundary automatically. An omitted selection returns `EXERCISE_REQUIRED`;
  there is no automatic recognition. Legacy `squat` also counts; other profiles are rejected.
- Keep **only the upload request's** timeout at **240 seconds** for local demo testing.
  Health/live requests keep their shorter timeout.
  Add a client test that the upload gets that separate timeout. Show an indeterminate
  “Analyzing video” state; the backend does not report progress percentages.
- Disable repeated submission while processing. HTTP 503 `VIDEO_PROCESSOR_BUSY` means wait
  and retry manually. Aborting the browser request does not stop native processing immediately;
  avoid automatic retries. The server keeps its extraction slot until processing unwinds.
- Retain the selected `File`/object URL for playback. The server returns no video URL and
  deletes temporary copies. Revoke old object URLs when the user changes the clip or leaves.
- Seek to `rep.startMs / 1000`. Ignore stale responses after a new selection. A complete
  result can still have null scores; do not show a worst rep until scores exist.
- This endpoint returns analysis, **not per-frame pose coordinates**. The implemented
  `/videos/analyze-with-pose` endpoint returns the matching pose track alongside analysis.
  Do not draw a fabricated skeleton from rep angles.
- A browser may not play every codec the backend decodes. If HEVC preview fails on the demo
  browser, export H.264 MP4 and re-analyze that exact exported clip for matching timestamps.
- `localhost` always refers to the browser's own computer. B can run this backend locally
  after the optional CV setup. Coordinate a same-network backend connection separately if
  needed; don't point B at A's `localhost` and expect it to cross computers.

## Limits, cleanup, and errors

Accepted extensions: MP4/MOV/WebM (case-insensitive). MIME headers are not trusted as codec
proof; the decoder must actually read the file. A file must be nonempty and <=250 MiB,
<=120 seconds, <=4K pixels, <=4096 on either axis, with usable monotonic timestamps and
fixed upright square-pixel dimensions. Sampling stays at most 15 fps / 1800 pose frames.
See VIDEO_SETUP.md for the decoder's other limits and uncertainty behavior.

The server copies the spooled upload in 1 MiB chunks to a uniquely named temporary folder,
using its own filename. It checks reported size and copied bytes. Success, input failures,
and model/analyzer exceptions remove that folder and close the multipart file. A process
crash or forced kill can leave operating-system temporary files; there is no durable storage.

Starlette parses/spools multipart data **before** this handler checks file size or the busy
slot. These are processing limits, not a hard network-body/disk quota. This endpoint is for
the local hackathon demo, not unrestricted public uploads. Native processing runs in a worker
thread so health requests remain responsive. A 180-second cooperative extraction deadline
is checked between native calls; it cannot forcibly interrupt a hung native call. The client
240-second timeout is also not a server cancellation mechanism. No queue/job API was added.

All application errors use `{"detail":{"code":"...","message":"..."}}`:

| HTTP | Code | Action |
| --- | --- | --- |
| 400 | `EXERCISE_REQUIRED`, `UNKNOWN_EXERCISE`, `EXERCISE_NOT_SUPPORTED` | Select `push-up` |
| 400 | `EMPTY_VIDEO`, `INVALID_VIDEO` | Choose a supported nonempty clip; read the message |
| 413 | `VIDEO_TOO_LARGE` | Trim/export below 250 MiB |
| 415 | `UNSUPPORTED_VIDEO_TYPE` | Use MP4/MOV/WebM |
| 422 | FastAPI validation `detail` array | Supply the multipart file/valid fields |
| 503 | `VIDEO_SETUP_REQUIRED` | Backend operator follows VIDEO_SETUP.md |
| 503 | `VIDEO_PROCESSOR_BUSY` | Wait for the current analysis to finish |
| 504 | `VIDEO_PROCESSING_TIMEOUT` | Use a shorter clip |
| 500 | `VIDEO_PROCESSING_FAILED` | Operator checks API terminal; response hides internal details |

Missing pose is normally a successful analysis response with `insufficient_data` or `partial`,
not an HTTP failure. It must never fall back to synthetic results. Health still only means
that the API is responding; it does not attest to model readiness.
