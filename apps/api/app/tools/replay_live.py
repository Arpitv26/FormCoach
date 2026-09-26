"""Replay a saved cumulative pose capture against a running API, without camera access."""

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.domain.analysis import AnalysisResponse
from app.domain.pose import LiveBatchRequest

MAX_CAPTURE_BYTES = 32 * 1024 * 1024
type SendBatch = Callable[[LiveBatchRequest], AnalysisResponse]


class ReplayError(Exception):
    """A transport or response-consistency failure, rather than a count mismatch."""


def load_capture(path: Path) -> LiveBatchRequest:
    with path.open("rb") as capture:
        data = capture.read(MAX_CAPTURE_BYTES + 1)
    if len(data) > MAX_CAPTURE_BYTES:
        raise ValueError("Capture exceeds 32 MiB; export at most 1800 sampled frames.")
    request = LiveBatchRequest.model_validate_json(data)
    if request.exercise_hint not in {"push-up", "squat"}:
        raise ValueError('Capture exerciseHint must be "push-up" or "squat".')
    if not request.frames:
        raise ValueError("Capture has no frames. Export poses from a recorded set first.")
    return request


def post_batch(base_url: str, batch: LiveBatchRequest) -> AnalysisResponse:
    request = Request(
        f"{base_url.rstrip('/')}/api/v1/live/analyze-batch",
        data=batch.model_dump_json(by_alias=True).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            return AnalysisResponse.model_validate_json(response.read())
    except HTTPError as error:
        raise ReplayError(
            f"API returned HTTP {error.code}; check the server terminal and capture format."
        ) from error
    except (URLError, TimeoutError) as error:
        raise ReplayError(
            "Could not reach the API within 15 seconds. Start Uvicorn and check --api-base-url."
        ) from error


def _check_response(batch: LiveBatchRequest, result: AnalysisResponse) -> None:
    if result.session_id != batch.session_id:
        raise ReplayError("API response belongs to a different session.")
    if result.source.type != "live" or result.source.duration_ms != batch.frames[-1].timestamp_ms:
        raise ReplayError("API response does not match the submitted frame time coverage.")
    if result.exercise is None or result.exercise.id != batch.exercise_hint:
        raise ReplayError("API response does not match the selected exercise.")


def replay_capture(
    capture: LiveBatchRequest,
    send: SendBatch,
    *,
    expected_reps: int,
    batch_frames: int = 15,
) -> dict:
    """Send growing snapshots, then repeat the final request to check determinism.

    Input poses and original timestamps are preserved. Requests run sequentially without
    real-time delays. The final file is treated as the whole set regardless of isFinal.
    A matching count is a comparison, not proof of event alignment or camera accuracy.
    """
    if not capture.frames or capture.exercise_hint not in {"push-up", "squat"}:
        raise ValueError("Replay requires a nonempty push-up or squat capture.")
    if type(batch_frames) is not int or not 1 <= batch_frames <= 1800:
        raise ValueError("batch_frames must be an integer from 1 to 1800.")
    if type(expected_reps) is not int or expected_reps < 0:
        raise ValueError("expected_reps must be a nonnegative integer.")
    frame_count = len(capture.frames)
    stops = [*range(batch_frames, frame_count, batch_frames), frame_count]
    previous: AnalysisResponse | None = None
    snapshots = []
    for stop in stops:
        batch = capture.model_copy(
            update={"frames": capture.frames[:stop], "is_final": stop == frame_count}
        )
        result = send(batch)
        _check_response(batch, result)
        if previous and result.reps[: len(previous.reps)] != previous.reps:
            raise ReplayError("A cumulative response dropped or changed an already completed rep.")
        snapshots.append(
            {
                "frameCount": stop,
                "timestampMs": batch.frames[-1].timestamp_ms,
                "status": result.status,
                "observedReps": result.summary.total_reps,
            }
        )
        previous = result

    repeated = send(batch)
    _check_response(batch, repeated)
    if repeated != result:
        raise ReplayError("Repeating the final request produced a different result.")

    count_matches = result.summary.total_reps == expected_reps
    outcome = "count_match"
    if result.status != "complete" or result.provenance.kind != "measured":
        outcome = "incomplete_analysis"
    elif not count_matches:
        outcome = "count_mismatch"
    return {
        "outcome": outcome,
        "expectedReps": expected_reps,
        "observedReps": result.summary.total_reps,
        "countMatches": count_matches,
        "cumulativeRepsStable": True,
        "finalReplayIdentical": True,
        "snapshots": snapshots,
        "analysis": result.model_dump(mode="json", by_alias=True),
        "reviewRequired": (
            "Compare each rep interval with the matching recording. A matching count alone "
            "does not establish correct timing, form assessment, or real-camera accuracy. "
            "The tool cannot verify whether input poses were captured or synthetic."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="Saved LiveBatchRequest JSON from one whole set")
    parser.add_argument(
        "--expected-reps", type=int, required=True, help="Human-counted completed reps"
    )
    parser.add_argument(
        "--batch-frames", type=int, default=15, help="New frames per cumulative POST"
    )
    parser.add_argument("--api-base-url", default="http://localhost:8000")
    args = parser.parse_args(argv)
    try:
        capture = load_capture(args.capture)
        report = replay_capture(
            capture,
            lambda batch: post_batch(args.api_base_url, batch),
            expected_reps=args.expected_reps,
            batch_frames=args.batch_frames,
        )
    except ValidationError as error:
        # Do not dump the pose capture into terminal logs on a malformed file/response.
        fields = ", ".join(".".join(map(str, item["loc"])) for item in error.errors()[:5])
        print(f"Invalid capture or API response near: {fields or 'JSON root'}.", file=sys.stderr)
        return 2
    except (OSError, ValueError, ReplayError) as error:
        print(f"Replay failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["outcome"] == "count_match" else 1


if __name__ == "__main__":
    sys.exit(main())
