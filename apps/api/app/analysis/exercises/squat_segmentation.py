"""Conservative squat segmentation from one consistently selected knee's 2D angle.

All thresholds are uncalibrated hackathon heuristics. This is not exercise recognition,
a form assessment, or a guarantee that a camera view supports the measurement.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace

from app.analysis.angle_segmentation import AngleCycleConfig, segment_angle_cycles
from app.analysis.exercises.squat import SQUAT_PROFILE
from app.analysis.rep_segmentation import (
    AngleSample,
    SegmentationResult,
)


@dataclass(frozen=True)
class SquatSegmentationConfig:
    standing_angle_deg: float = SQUAT_PROFILE.thresholds["standingKneeAngleDeg"]
    bottom_angle_deg: float = SQUAT_PROFILE.thresholds["bottomKneeAngleDeg"]
    hysteresis_deg: float = 10
    minimum_phase_ms: int = 150
    minimum_rep_ms: int = 800
    maximum_rep_ms: int = 15_000
    maximum_gap_ms: int = 300
    smoothing_window: int = 3

    def __post_init__(self) -> None:
        self.as_angle_config()

    def as_angle_config(self) -> AngleCycleConfig:
        options = asdict(self)
        options["extended_angle_deg"] = options.pop("standing_angle_deg")
        options["flexed_angle_deg"] = options.pop("bottom_angle_deg")
        return AngleCycleConfig(**options)


def segment_squats(
    samples: Sequence[AngleSample], *, config: SquatSegmentationConfig | None = None
) -> SegmentationResult:
    """Preserve the squat interface while sharing tested angle-cycle mechanics."""
    result = segment_angle_cycles(
        samples, config=(config or SquatSegmentationConfig()).as_angle_config()
    )
    return (
        replace(result, current_phase="standing") if result.current_phase == "extended" else result
    )
