"""Bounded temporary uploads feed the same analyzer as live pose batches."""

from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Protocol
from uuid import uuid4

from fastapi import UploadFile

from app.analysis.exercises.registry import PROFILES
from app.analysis.interfaces import MovementAnalyzer
from app.analysis.movement import MOVEMENTS
from app.domain.analysis import AnalysisResponse, Source
from app.domain.video import PoseTrack, VideoAnalysisResponse
from app.services.mediapipe_pose import MAX_VIDEO_BYTES
from app.services.pose_provider import PoseProvider

_EXTRACTION_GATE = Lock()


class VideoRequestError(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code


class VideoProcessor(Protocol):
    def analyze(self, file: UploadFile, exercise_hint: str | None) -> AnalysisResponse: ...

    def analyze_with_pose(
        self, file: UploadFile, exercise_hint: str | None
    ) -> VideoAnalysisResponse: ...


class UploadedVideoProcessor:
    def __init__(self, provider: PoseProvider, analyzer: MovementAnalyzer) -> None:
        self.provider = provider
        self.analyzer = analyzer
        # One native extraction per API process; reject overlapping work rather than queue it.
        self._gate = _EXTRACTION_GATE

    def analyze(self, file: UploadFile, exercise_hint: str | None) -> AnalysisResponse:
        return self.analyze_with_pose(file, exercise_hint).analysis

    def analyze_with_pose(
        self, file: UploadFile, exercise_hint: str | None
    ) -> VideoAnalysisResponse:
        if not exercise_hint:
            raise VideoRequestError(
                400, "EXERCISE_REQUIRED", "Select an exercise before uploading."
            )
        if exercise_hint not in PROFILES:
            raise VideoRequestError(400, "UNKNOWN_EXERCISE", "Use a registered exercise ID.")
        if exercise_hint not in MOVEMENTS:
            raise VideoRequestError(
                400, "EXERCISE_NOT_SUPPORTED", "Video counting is not available for this exercise."
            )
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in {".mp4", ".mov", ".webm"}:
            raise VideoRequestError(415, "UNSUPPORTED_VIDEO_TYPE", "Use an MP4, MOV, or WebM file.")
        if file.size is not None and file.size > MAX_VIDEO_BYTES:
            raise VideoRequestError(413, "VIDEO_TOO_LARGE", "Video must be at most 250 MiB.")
        if not self._gate.acquire(blocking=False):
            raise VideoRequestError(
                503, "VIDEO_PROCESSOR_BUSY", "Another video is processing. Wait and try again."
            )
        try:
            # Never use the supplied filename as a filesystem path. Both this copy and
            # Starlette's multipart spool are closed on success and failure.
            with TemporaryDirectory(prefix="formcoach-upload-") as directory:
                path = Path(directory) / f"input{suffix}"
                self._copy_upload(file, path)
                sequence = self.provider.extract(path)
                result = self.analyzer.analyze(
                    sequence.frames,
                    session_id=str(uuid4()),
                    source=Source(type="upload", duration_ms=sequence.duration_ms),
                    image_width=sequence.image_width,
                    image_height=sequence.image_height,
                    profile=PROFILES[exercise_hint],
                    is_final=True,
                )
                result.limitations.append(
                    "Poses extracted with MediaPipe Pose Landmarker Full. No-pose/multiple-person "
                    "frames are unavailable. Model estimates and rep counts need video review."
                )
                return VideoAnalysisResponse(
                    analysis=result,
                    pose_track=PoseTrack(
                        image_width=sequence.image_width,
                        image_height=sequence.image_height,
                        duration_ms=sequence.duration_ms,
                        frames=sequence.frames,
                    ),
                )
        finally:
            self._gate.release()

    @staticmethod
    def _copy_upload(file: UploadFile, path: Path) -> None:
        file.file.seek(0)
        size = 0
        with path.open("wb") as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_VIDEO_BYTES:
                    raise VideoRequestError(
                        413, "VIDEO_TOO_LARGE", "Video must be at most 250 MiB."
                    )
                target.write(chunk)
        if size == 0:
            raise VideoRequestError(400, "EMPTY_VIDEO", "Choose a nonempty video file.")
