"""Selected lat-pulldown elbow cycles; descriptive 2D measurements, not form grades."""

from collections.abc import Sequence

from app.analysis.angle_segmentation import AngleCycleConfig, segment_angle_cycles
from app.analysis.exercises.base import ExerciseProfile
from app.analysis.rep_segmentation import AngleSample, SegmentationResult

LAT_PULLDOWN_PROFILE = ExerciseProfile(
    id="lat-pulldown",
    name="Lat pulldown",
    relevant_joints=tuple(
        f"{side}_{joint}" for side in ("left", "right") for joint in ("shoulder", "elbow", "wrist")
    ),
    camera_orientation="Side view with shoulder, elbow and wrist visible throughout.",
    phases=("extended", "descent", "bottom", "ascent"),
    metrics=("observedElbowExcursion", "duration"),
    rules=(),
    coaching_cues=(),
    thresholds={"returnElbowAngleDeg": 120, "pulledElbowAngleDeg": 70, "minimumPhaseMs": 100},
    status="example",
)


def segment_lat_pulldowns(samples: Sequence[AngleSample]) -> SegmentationResult:
    return segment_angle_cycles(
        samples,
        config=AngleCycleConfig(
            extended_angle_deg=LAT_PULLDOWN_PROFILE.thresholds["returnElbowAngleDeg"],
            flexed_angle_deg=LAT_PULLDOWN_PROFILE.thresholds["pulledElbowAngleDeg"],
            minimum_phase_ms=LAT_PULLDOWN_PROFILE.thresholds["minimumPhaseMs"],
            independent_phase_confirmation=True,
        ),
    )
