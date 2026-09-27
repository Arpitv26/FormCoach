"""HTTP/upload lifecycle tests; synthetic poses keep native CV optional in CI."""

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from threading import Event
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException, UploadFile
from test_pushup_analysis import pushup_request

from app.analysis.movement import RuleBasedAnalyzer
from app.api.routes.videos import analyze_video, get_video_processor
from app.core.config import API_ROOT, get_settings
from app.domain.analysis import AnalysisResponse
from app.domain.pose import LiveBatchRequest
from app.domain.video import VideoAnalysisResponse
from app.services import video_processor as service
from app.services.mediapipe_pose import (
    MediaPipePoseProvider,
    VideoInputError,
    VideoProcessingTimeout,
    VideoSetupError,
)
from app.services.pose_provider import PoseSequence


@pytest.fixture
def upload_service(client):
    capture = LiveBatchRequest.model_validate(pushup_request(final=True))
    state = SimpleNamespace(
        paths=[], error=None, sequence=PoseSequence(capture.frames, 1280, 720, 2450)
    )

    class Provider:
        def extract(self, path):
            state.paths.append(path)
            assert path.read_bytes() == b"synthetic video bytes"
            if state.error:
                raise state.error
            return state.sequence

    processor = service.UploadedVideoProcessor(Provider(), RuleBasedAnalyzer())
    client.app.dependency_overrides[get_video_processor] = lambda: processor
    yield processor, state
    client.app.dependency_overrides.clear()
    assert all(not path.parent.exists() for path in state.paths)


def post(client, *, name="clip.MOV", content=b"synthetic video bytes", hint="push-up"):
    return client.post(
        "/api/v1/videos/analyze",
        files={"file": (name, content, "application/octet-stream")},
        data={} if hint is None else {"exerciseHint": hint},
    )


def test_upload_preserves_measured_response_and_uses_unique_sessions(client, upload_service):
    _, state = upload_service
    first = post(client, name="../../private/clip.MOV")
    assert first.status_code == 200
    result = AnalysisResponse.model_validate(first.json())
    assert result.source.type == "upload" and result.source.duration_ms == 2450
    assert result.status == "complete" and result.summary.total_reps == 1
    assert result.exercise.id == "push-up" and result.exercise.confidence is None
    assert result.provenance.kind == "measured"
    assert result.summary.overall_score is None and result.reps[0].score is None
    assert result.reps[0].start_ms == 500 and result.reps[0].end_ms == 2100
    assert result.reps[0].measurements["minSmoothedLeftElbowAngleDeg"] == 90
    assert not result.issues
    assert state.paths[0].name == "input.mov"
    assert not state.paths[0].parent.exists()
    UUID(result.session_id)
    second = AnalysisResponse.model_validate(post(client).json())
    assert second.session_id != result.session_id
    assert second.reps == result.reps


@pytest.mark.parametrize(
    "name,content,hint,status,code",
    [
        ("clip.mov", b"", "push-up", 400, "EMPTY_VIDEO"),
        ("clip.txt", b"video", "push-up", 415, "UNSUPPORTED_VIDEO_TYPE"),
        ("clip.mov", b"video", None, 400, "EXERCISE_REQUIRED"),
        ("clip.mov", b"video", "magic", 400, "UNKNOWN_EXERCISE"),
        ("clip.mov", b"video", "lunge", 400, "EXERCISE_NOT_SUPPORTED"),
    ],
)
def test_invalid_requests_never_start_cv(client, upload_service, name, content, hint, status, code):
    _, state = upload_service
    response = post(client, name=name, content=content, hint=hint)
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert not state.paths


def test_missing_multipart_file_is_validation_error(client):
    assert (
        client.post("/api/v1/videos/analyze", data={"exerciseHint": "push-up"}).status_code == 422
    )


@pytest.mark.parametrize(
    "error,status,code",
    [
        (VideoInputError("Video could not be decoded."), 400, "INVALID_VIDEO"),
        (VideoSetupError("Pose model is missing."), 503, "VIDEO_SETUP_REQUIRED"),
        (
            VideoProcessingTimeout("Processing exceeded 180 seconds."),
            504,
            "VIDEO_PROCESSING_TIMEOUT",
        ),
        (RuntimeError("private diagnostic /private/model.task"), 500, "VIDEO_PROCESSING_FAILED"),
        (OSError("private filesystem detail"), 500, "VIDEO_PROCESSING_FAILED"),
    ],
)
def test_provider_errors_cleanup_and_allow_retry(client, upload_service, error, status, code):
    _, state = upload_service
    state.error = error
    response = post(client)
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert "private" not in response.text
    assert not state.paths[-1].parent.exists()
    state.error = None
    assert post(client).status_code == 200


def test_no_detected_pose_remains_unknown(client, upload_service):
    _, state = upload_service
    state.sequence = PoseSequence(
        [frame.model_copy(update={"landmarks": []}) for frame in state.sequence.frames],
        1280,
        720,
        2450,
    )
    response = post(client)
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"
    assert response.json()["summary"]["totalReps"] is None


@pytest.mark.parametrize("declared_size", [None, 1, 100])
def test_size_limit_checks_metadata_and_actual_bytes(tmp_path, monkeypatch, declared_size):
    monkeypatch.setattr(service, "MAX_VIDEO_BYTES", 10)
    real_temp = service.TemporaryDirectory
    monkeypatch.setattr(service, "TemporaryDirectory", lambda **kw: real_temp(dir=tmp_path, **kw))
    processor = service.UploadedVideoProcessor(None, None)  # CV must never be reached.
    upload = UploadFile(BytesIO(b"x" * 11), filename="clip.mov", size=declared_size)
    with pytest.raises(service.VideoRequestError) as error:
        processor.analyze(upload, "push-up")
    assert error.value.status == 413
    assert not list(tmp_path.iterdir())
    upload.file.close()


@pytest.mark.parametrize("failure", [False, True])
def test_route_closes_multipart_spool(upload_service, failure):
    processor, state = upload_service
    if failure:
        state.error = VideoInputError("broken")
    upload = UploadFile(BytesIO(b"synthetic video bytes"), filename="clip.mov")
    if failure:
        with pytest.raises(HTTPException) as error:
            analyze_video(upload, processor, "push-up")
        assert error.value.status_code == 400
    else:
        analyze_video(upload, processor, "push-up")
    assert upload.file.closed


def test_analyzer_failure_also_cleans_video_and_releases_slot(client, upload_service):
    processor, state = upload_service

    class BrokenAnalyzer:
        def analyze(self, *_args, **_kwargs):
            raise RuntimeError("analysis failed")

    processor.analyzer = BrokenAnalyzer()
    response = post(client)
    assert response.status_code == 500
    assert not state.paths[-1].parent.exists()
    processor.analyzer = RuleBasedAnalyzer()
    assert post(client).status_code == 200


def test_missing_model_is_service_unavailable_without_native_imports(client, tmp_path):
    processor = service.UploadedVideoProcessor(
        MediaPipePoseProvider(tmp_path / "absent.task"), RuleBasedAnalyzer()
    )
    client.app.dependency_overrides[get_video_processor] = lambda: processor
    try:
        response = post(client)
        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "VIDEO_SETUP_REQUIRED"
    finally:
        client.app.dependency_overrides.clear()


def test_slow_upload_does_not_block_health_and_second_upload_is_busy(client, upload_service):
    processor, state = upload_service
    entered, release = Event(), Event()
    original = processor.provider.extract

    def waiting_provider(path):
        entered.set()
        assert release.wait(5), "Test did not release the slow provider"
        return original(path)

    processor.provider.extract = waiting_provider
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(post, client)
        try:
            assert entered.wait(5)
            health = pool.submit(client.get, "/api/v1/health").result(timeout=2)
            assert health.status_code == 200
            second = pool.submit(post, client).result(timeout=2)
            assert second.status_code == 503
            assert second.json()["detail"]["code"] == "VIDEO_PROCESSOR_BUSY"
        finally:
            release.set()
        assert first.result(timeout=5).status_code == 200
    assert post(client).status_code == 200


def test_model_path_is_relative_to_api_root(monkeypatch):
    monkeypatch.setenv("POSE_MODEL_PATH", "artifacts/test.task")
    assert get_settings().pose_model_path == API_ROOT / "artifacts/test.task"
    monkeypatch.setenv("POSE_MODEL_PATH", "/tmp/custom.task")
    assert get_settings().pose_model_path == Path("/tmp/custom.task")


def test_overlay_upload_extracts_once_and_matches_analysis(client, upload_service):
    _, state = upload_service
    response = client.post(
        "/api/v1/videos/analyze-with-pose",
        files={"file": ("clip.mov", b"synthetic video bytes")},
        data={"exerciseHint": "push-up"},
    )
    assert response.status_code == 200
    result = VideoAnalysisResponse.model_validate(response.json())
    assert len(state.paths) == 1
    assert result.pose_track.frames == state.sequence.frames
    assert (result.pose_track.image_width, result.pose_track.image_height) == (1280, 720)
    assert result.pose_track.duration_ms == result.analysis.source.duration_ms
    original = AnalysisResponse.model_validate(post(client).json())
    assert result.analysis.reps == original.reps
    assert result.analysis.summary == original.summary
    assert "poseTrack" not in post(client).json()


def test_overlay_preserves_empty_frames_and_portrait_dimensions(client, upload_service):
    _, state = upload_service
    state.sequence = PoseSequence(
        [frame.model_copy(update={"landmarks": []}) for frame in state.sequence.frames],
        720,
        1280,
        2450,
    )
    response = client.post(
        "/api/v1/videos/analyze-with-pose",
        files={"file": ("clip.mov", b"synthetic video bytes")},
        data={"exerciseHint": "push-up"},
    )
    result = VideoAnalysisResponse.model_validate(response.json())
    assert result.pose_track.image_width == 720
    assert result.pose_track.image_height == 1280
    assert all(frame.landmarks == [] for frame in result.pose_track.frames)
    assert result.analysis.summary.total_reps is None


def test_overlay_error_closes_spool_and_releases_gate(upload_service):
    from app.api.routes.videos import analyze_video_with_pose

    processor, state = upload_service
    state.error = VideoInputError("broken")
    upload = UploadFile(BytesIO(b"synthetic video bytes"), filename="clip.mov")
    with pytest.raises(HTTPException):
        analyze_video_with_pose(upload, processor, "push-up")
    assert upload.file.closed
    assert processor._gate.acquire(blocking=False)
    processor._gate.release()


def test_visual_review_uses_ephemeral_frames_and_cleanup_without_changing_count(
    client, upload_service
):
    from app.domain.visual_review import VisualReview

    processor, state = upload_service
    state.sequence.visual_frames.extend([(0, "private-image"), (1000, "private-image-2")])
    calls = []

    class Reviewer:
        def review(self, path, analysis, frames):
            assert path.exists() and analysis.summary.total_reps == 1
            assert frames == state.sequence.visual_frames
            calls.append(path)
            return VisualReview(
                status="unavailable",
                model="test",
                sampled_timestamps_ms=[0, 1000],
                findings=[],
                limitations=["Test failure preserves measurements."],
            )

    processor.visual_reviewer = Reviewer()
    result = post(client)
    assert result.status_code == 200
    assert result.json()["summary"]["totalReps"] == 1
    assert result.json()["visualReview"]["status"] == "unavailable"
    assert "private-image" not in result.text and len(calls) == 1
    assert not calls[0].exists()
