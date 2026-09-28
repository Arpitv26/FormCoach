import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import TypeAdapter
from test_pushup_analysis import pushup_request

from app.analysis.movement import RuleBasedAnalyzer
from app.api.routes.videos import get_video_processor
from app.domain.pose import LiveBatchRequest
from app.services import isolated_pose
from app.services.mediapipe_pose import VideoProcessingTimeout, VideoSetupError
from app.services.pose_provider import PoseSequence
from app.services.video_processor import UploadedVideoProcessor


def test_worker_round_trip_preserves_poses_images_and_options(monkeypatch, tmp_path):
    frames = LiveBatchRequest.model_validate(pushup_request(final=True)).frames
    sequence = PoseSequence(frames, 1280, 720, 2450, [(0, "sample-jpeg")])
    outputs = []

    def run(command, **kwargs):
        assert command[-2:] == ["--visual", "--dominant"]
        assert kwargs["timeout"] == 190
        output = Path(command[5])
        outputs.append(output)
        output.write_text(
            json.dumps({"sequence": TypeAdapter(PoseSequence).dump_python(sequence, mode="json")})
        )
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(isolated_pose.subprocess, "run", run)
    provider = isolated_pose.IsolatedMediaPipePoseProvider(
        tmp_path / "model.task", include_visual_frames=True, allow_dominant_pose=True
    )
    assert provider.extract(tmp_path / "clip.mov") == sequence
    assert all(not output.parent.exists() for output in outputs)


def test_real_worker_preserves_setup_errors(tmp_path):
    clip = tmp_path / "clip.mov"
    clip.write_bytes(b"nonempty")
    provider = isolated_pose.IsolatedMediaPipePoseProvider(tmp_path / "missing.task")
    with pytest.raises(VideoSetupError, match="Pose model is missing"):
        provider.extract(clip)


def test_worker_timeout_cleans_temporary_output(monkeypatch, tmp_path):
    outputs = []

    def timeout(command, **kwargs):
        outputs.append(Path(command[5]))
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(isolated_pose.subprocess, "run", timeout)
    provider = isolated_pose.IsolatedMediaPipePoseProvider(tmp_path / "model.task")
    with pytest.raises(VideoProcessingTimeout, match="190 seconds"):
        provider.extract(tmp_path / "clip.mov")
    assert all(not output.parent.exists() for output in outputs)


def test_terminated_native_worker_does_not_kill_api_or_lock_future_uploads(
    client, monkeypatch, tmp_path
):
    real_run = subprocess.run
    failed = False

    def run(command, **kwargs):
        nonlocal failed
        if not failed:
            failed = True
            return real_run(
                [sys.executable, "-c", "import os, signal; os.kill(os.getpid(), signal.SIGKILL)"],
                **kwargs,
            )
        Path(command[5]).write_text(
            json.dumps({"error": "input", "message": "Video could not be decoded."})
        )
        return subprocess.CompletedProcess(command, 0, b"", b"")

    monkeypatch.setattr(isolated_pose.subprocess, "run", run)
    processor = UploadedVideoProcessor(
        isolated_pose.IsolatedMediaPipePoseProvider(tmp_path / "model.task"), RuleBasedAnalyzer()
    )
    client.app.dependency_overrides[get_video_processor] = lambda: processor
    try:

        def upload():
            return client.post(
                "/api/v1/videos/analyze-with-pose",
                files={"file": ("clip.mov", b"video")},
                data={"exerciseHint": "push-up"},
            )

        first = upload()
        assert first.status_code == 503
        assert first.json()["detail"]["code"] == "VIDEO_PROCESSING_UNAVAILABLE"
        assert client.get("/api/v1/health").status_code == 200
        assert client.post("/api/v1/live/analyze-batch", json=pushup_request()).status_code == 200
        assert upload().status_code == 400  # A fresh worker runs; the extraction lock was released.
    finally:
        client.app.dependency_overrides.clear()
