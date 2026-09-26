"""Local recorded-video checkpoint; writes poses and analysis into a new output folder."""

import argparse
import sys
from pathlib import Path
from uuid import uuid4

from app.analysis.exercises.registry import PROFILES
from app.analysis.movement import RuleBasedAnalyzer
from app.domain.analysis import Source
from app.domain.pose import LiveBatchRequest
from app.services.mediapipe_pose import MediaPipePoseProvider


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument(
        "--model", type=Path, default=Path("artifacts/models/pose_landmarker_full.task")
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="New folder, preferably in artifacts/"
    )
    args = parser.parse_args(argv)
    if args.output.exists():
        print(
            "Choose a new --output folder; previous results will not be overwritten.",
            file=sys.stderr,
        )
        return 2
    try:
        print("Extracting push-up poses locally. This may take a minute...", file=sys.stderr)
        sequence = MediaPipePoseProvider(args.model).extract(args.video)
        capture = LiveBatchRequest(
            session_id=str(uuid4()),
            exercise_hint="push-up",
            frames=sequence.frames,
            image_width=sequence.image_width,
            image_height=sequence.image_height,
            is_final=True,
        )
        analysis = RuleBasedAnalyzer().analyze(
            sequence.frames,
            session_id=capture.session_id,
            source=Source(type="upload", duration_ms=sequence.duration_ms),
            image_width=sequence.image_width,
            image_height=sequence.image_height,
            profile=PROFILES["push-up"],
            is_final=True,
        )
        analysis.limitations.append(
            "Poses extracted locally with MediaPipe Pose Landmarker Full. No-pose/multiple-person "
            "frames are unavailable. Model estimates and rep counts need comparison with the video."
        )
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "poses.json").write_text(
            capture.model_dump_json(by_alias=True, indent=2) + "\n"
        )
        (args.output / "analysis.json").write_text(
            analysis.model_dump_json(by_alias=True, indent=2) + "\n"
        )
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Video analysis failed: {error}", file=sys.stderr)
        return 2
    count = analysis.summary.total_reps
    print(f"Status: {analysis.status}; observed reps: {count if count is not None else 'unknown'}")
    print(f"Saved poses.json and analysis.json in {args.output}")
    print(
        "Compare counts and rep timestamps with the recording before calling the result accurate."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
