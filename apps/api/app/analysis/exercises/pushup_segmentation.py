"""Push-up elbow cycles; provisional thresholds, not a validated form assessment."""

from collections.abc import Sequence
from dataclasses import replace

from app.analysis.angle_segmentation import AngleCycleConfig, segment_angle_cycles
from app.analysis.exercises.pushup import PUSHUP_PROFILE
from app.analysis.rep_segmentation import AngleSample, SegmentationResult


def segment_pushups(samples: Sequence[AngleSample]) -> SegmentationResult:
    config = AngleCycleConfig(
        extended_angle_deg=PUSHUP_PROFILE.thresholds["topElbowAngleDeg"],
        flexed_angle_deg=PUSHUP_PROFILE.thresholds["bottomElbowAngleDeg"],
        minimum_phase_ms=PUSHUP_PROFILE.thresholds["minimumPhaseMs"],
        independent_phase_confirmation=True,
    )
    result = segment_angle_cycles(samples, config=config)
    return replace(result, current_phase="top") if result.current_phase == "extended" else result
