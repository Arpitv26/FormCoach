"""Keep native video/graphics failures outside the HTTP server process."""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import TypeAdapter

from app.services.mediapipe_pose import (
    MediaPipePoseProvider,
    VideoInputError,
    VideoProcessingTimeout,
    VideoSetupError,
)
from app.services.pose_provider import PoseSequence

logger = logging.getLogger(__name__)
_SEQUENCE = TypeAdapter(PoseSequence)
_ERRORS = {
    "setup": VideoSetupError,
    "timeout": VideoProcessingTimeout,
    "input": VideoInputError,
}


class VideoWorkerCrashed(RuntimeError):
    """A native worker exited without a usable result; the API is still healthy."""


class IsolatedMediaPipePoseProvider(MediaPipePoseProvider):
    def extract(self, video_path: Path) -> PoseSequence:
        with TemporaryDirectory(prefix="formcoach-pose-") as directory:
            output = Path(directory) / "result.json"
            command = [
                sys.executable,
                "-m",
                "app.services.isolated_pose",
                str(video_path.resolve()),
                str(self.model_path.resolve()),
                str(output),
            ]
            if self.include_visual_frames:
                command.append("--visual")
            if self.allow_dominant_pose:
                command.append("--dominant")
            try:
                completed = subprocess.run(
                    command,
                    cwd=Path(__file__).resolve().parents[2],
                    capture_output=True,
                    timeout=190,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise VideoProcessingTimeout("Video extraction exceeded 190 seconds.") from error
            if completed.returncode != 0:
                logger.error(
                    "Pose worker exited %s: %s",
                    completed.returncode,
                    completed.stderr[-4000:].decode(errors="replace"),
                )
                raise VideoWorkerCrashed("Native video processing stopped unexpectedly.")
            payload = json.loads(output.read_text())
            if "error" in payload:
                raise _ERRORS[payload["error"]](payload["message"])
            return _SEQUENCE.validate_python(payload["sequence"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--visual", action="store_true")
    parser.add_argument("--dominant", action="store_true")
    args = parser.parse_args()
    provider = MediaPipePoseProvider(
        args.model, include_visual_frames=args.visual, allow_dominant_pose=args.dominant
    )
    try:
        payload = {"sequence": _SEQUENCE.dump_python(provider.extract(args.video), mode="json")}
    except VideoSetupError as error:
        payload = {"error": "setup", "message": str(error)}
    except VideoProcessingTimeout as error:
        payload = {"error": "timeout", "message": str(error)}
    except VideoInputError as error:
        payload = {"error": "input", "message": str(error)}
    args.output.write_text(json.dumps(payload))


if __name__ == "__main__":
    main()
