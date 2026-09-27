"""Observed bent-to-extended presses. Reset at bent arms before another press."""

from collections import deque
from collections.abc import Sequence
from statistics import median

from app.analysis.exercises.base import ExerciseProfile
from app.analysis.rep_segmentation import AngleSample, RepSegment, SegmentationResult

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
    for before, after in zip(samples, samples[1:], strict=False):
        if after.timestamp_ms <= before.timestamp_ms:
            raise ValueError("Angle sample timestamps must strictly increase")
    t = INCLINE_PRESS_PROFILE.thresholds
    window = deque(maxlen=3)
    phase = "unknown"
    reps = []
    previous = None
    last = None
    zones = {}
    start = None
    minimum = maximum = bottom_ms = measurement_start = 0
    breaks = 0
    for sample in samples:
        timestamp, raw = sample.timestamp_ms, sample.angle_deg
        gap = previous is not None and timestamp - previous > t["maximumGapMs"]
        expired = start is not None and timestamp - start > t["maximumPressMs"]
        previous = timestamp
        if raw is None or gap or expired:
            if window and (raw is None or gap):
                breaks += 1
            window.clear()
            phase, last, start = "unknown", None, None
            zones.clear()
            if raw is None:
                continue
        window.append(raw)
        if len(window) < 3:
            continue
        last = float(median(window))
        conditions = {
            "bent": raw <= t["bentElbowAngleDeg"],
            "pressing": raw >= t["bentElbowAngleDeg"] + t["hysteresisDeg"],
            "extended": raw >= t["extendedElbowAngleDeg"],
        }
        for zone, condition in conditions.items():
            if condition:
                zones.setdefault(zone, timestamp)
            else:
                zones.pop(zone, None)
        confirmed = {
            zone for zone, since in zones.items() if timestamp - since >= t["minimumPhaseMs"]
        }
        if phase in {"unknown", "top"}:
            if "bent" in confirmed and last <= t["bentElbowAngleDeg"]:
                phase = "bottom"
                start = zones["bent"]
                measurement_start = bottom_ms = timestamp
                minimum = maximum = last
            continue
        if last < minimum:
            minimum, bottom_ms = last, timestamp
        maximum = max(maximum, last)
        if phase == "bottom":
            if "pressing" not in confirmed or last < t["bentElbowAngleDeg"] + t["hysteresisDeg"]:
                continue
            phase = "ascent"
        if phase == "ascent":
            if "bent" in confirmed and last <= t["bentElbowAngleDeg"]:
                phase = "bottom"  # Incomplete press, no manufactured rep.
                start = zones["bent"]
                measurement_start = bottom_ms = timestamp
                minimum = maximum = last
                continue
            if "extended" in confirmed and last >= t["extendedElbowAngleDeg"]:
                if timestamp - start >= t["minimumPressMs"]:
                    reps.append(
                        RepSegment(start, bottom_ms, timestamp, minimum, maximum, measurement_start)
                    )
                phase, start = "top", None
    return SegmentationResult(tuple(reps), phase, last, breaks)
