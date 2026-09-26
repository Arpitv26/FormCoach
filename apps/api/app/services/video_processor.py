from typing import Protocol

from fastapi import UploadFile

from app.domain.analysis import AnalysisResponse


class VideoProcessor(Protocol):
    async def analyze(self, file: UploadFile, exercise_hint: str | None) -> AnalysisResponse:
        """Future extraction -> PoseFrame sequence -> same MovementAnalyzer as live."""
        ...


class PlaceholderVideoProcessor:
    async def analyze(self, file: UploadFile, exercise_hint: str | None) -> AnalysisResponse:
        raise NotImplementedError("Video pose extraction is not implemented in this bootstrap.")
