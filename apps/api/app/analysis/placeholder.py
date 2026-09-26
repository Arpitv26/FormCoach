from collections.abc import Sequence

from app.analysis.exercises.base import ExerciseProfile
from app.domain.analysis import (
    AnalysisResponse,
    CameraQuality,
    Exercise,
    Provenance,
    SessionMetrics,
    Source,
    Summary,
)
from app.domain.pose import PoseFrame


class PlaceholderAnalyzer:
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
        """Accept the contract without claiming to have analyzed any movement."""
        return AnalysisResponse(
            contract_version="1.0",
            session_id=session_id,
            status="not_implemented",
            provenance=Provenance(kind="placeholder", label="Movement analysis is not implemented"),
            source=source,
            exercise=(
                Exercise(id=profile.id, name=profile.name, confidence=None) if profile else None
            ),
            camera_quality=CameraQuality(
                score=None,
                full_body_visible=None,
                issues=["Camera readiness has not been evaluated."],
            ),
            summary=Summary(
                overall_score=None,
                total_reps=None,
                primary_focus=None,
                headline="Pose batch received. Movement analysis is not implemented yet.",
            ),
            metrics=SessionMetrics(
                range_of_motion=None,
                symmetry=None,
                tempo=None,
                stability=None,
                consistency=None,
            ),
            reps=[],
            issues=[],
            timeline=[],
            scoring=None,
            limitations=[
                "No exercise, repetitions, joint angles, or form issues were measured.",
                "The exercise hint is a user selection, not a detected classification.",
            ],
        )
