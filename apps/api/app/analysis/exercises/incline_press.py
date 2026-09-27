"""Observed bent-to-extended presses. Reset at bent arms before another press."""

from collections.abc import Sequence

from app.analysis.exercises.base import ExerciseProfile
from app.analysis.rep_segmentation import AngleSample, SegmentationResult
from app.analysis.rising_segmentation import RisingConfig, segment_rising_angles

INCLINE_PRESS_PROFILE = ExerciseProfile(
    id="incline-dumbbell-bench-press",
    name="Incline dumbbell bench press",
    relevant_joints=tuple(
        f"{side}_{joint}" for side in ("left", "right") for joint in ("shoulder", "elbow", "wrist")
    ),
    camera_orientation="Side or oblique view with one shoulder, elbow and wrist visible.",
    phases=("bottom", "ascent", "top"),
    metrics=("observedElbowExcursion", "duration"),
    rules=(),
    coaching_cues=(),
    thresholds={
        "bentElbowAngleDeg": 100,
        "extendedElbowAngleDeg": 150,
        "hysteresisDeg": 10,
        "minimumPhaseMs": 100,
        "minimumPressMs": 300,
        "maximumPressMs": 15000,
        "maximumGapMs": 300,
    },
    status="example",
)


def segment_incline_presses(samples: Sequence[AngleSample]) -> SegmentationResult:
    """Count the visible press on extension; lowering rearms but never counts by itself.

    The time window starts at the first <=100° sample of confirmed bent arms, and
    ends on confirmed >=150° extension. Extrema begin at bent-position confirmation.
    These are bent-to-extended intervals (including pauses), not full cycle times.
    Missing data/gaps reset the unfinished press. Never switch arms to complete it.
    """
    t = INCLINE_PRESS_PROFILE.thresholds
    return segment_rising_angles(
        samples,
        config=RisingConfig(
            ready_angle_deg=t["bentElbowAngleDeg"],
            target_angle_deg=t["extendedElbowAngleDeg"],
            hysteresis_deg=t["hysteresisDeg"],
            minimum_phase_ms=t["minimumPhaseMs"],
            minimum_rep_ms=t["minimumPressMs"],
            maximum_rep_ms=t["maximumPressMs"],
            maximum_gap_ms=t["maximumGapMs"],
        ),
    )
