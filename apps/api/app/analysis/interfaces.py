from collections.abc import Sequence
from typing import Protocol

from app.analysis.exercises.base import ExerciseProfile
from app.domain.analysis import AnalysisResponse, Source
from app.domain.pose import PoseFrame


class MovementAnalyzer(Protocol):
    def analyze(
        self,
        frames: Sequence[PoseFrame],
        *,
        session_id: str,
        source: Source,
        image_width: int,
        image_height: int,
        profile: ExerciseProfile | None,
        is_final: bool,
    ) -> AnalysisResponse:
        """Shared boundary for live/upload inputs and heuristic/future ML analyzers."""
        ...
