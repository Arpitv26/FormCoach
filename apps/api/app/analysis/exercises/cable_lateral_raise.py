"""Visible arm lifts; shoulder geometry is projected 2D, not anatomical abduction."""

from collections.abc import Sequence

from app.analysis.exercises.base import ExerciseProfile
from app.analysis.rep_segmentation import AngleSample, SegmentationResult
from app.analysis.rising_segmentation import RisingConfig, segment_rising_angles

CABLE_LATERAL_RAISE_PROFILE = ExerciseProfile(
    id="cable-lateral-raise",
    name="Cable lateral raise",
    relevant_joints=tuple(
        f"{side}_{joint}" for side in ("left", "right") for joint in ("hip", "shoulder", "elbow")
    ),
    camera_orientation="Keep the working arm and torso visible; back-view counting is unreliable.",
    phases=("bottom", "ascent", "top"),
    metrics=("observedShoulderExcursion", "duration"),
    rules=(),
    coaching_cues=(),
    thresholds={
        "loweredShoulderAngleDeg": 30,
        "raisedShoulderAngleDeg": 60,
        "hysteresisDeg": 10,
        "minimumPhaseMs": 100,
    },
    status="example",
)


def segment_cable_lateral_raises(samples: Sequence[AngleSample]) -> SegmentationResult:
    t = CABLE_LATERAL_RAISE_PROFILE.thresholds
    return segment_rising_angles(
        samples,
        config=RisingConfig(
            ready_angle_deg=t["loweredShoulderAngleDeg"],
            target_angle_deg=t["raisedShoulderAngleDeg"],
            hysteresis_deg=t["hysteresisDeg"],
            minimum_phase_ms=t["minimumPhaseMs"],
        ),
    )
