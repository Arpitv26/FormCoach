"""Descriptive shoulder–hip–ankle geometry, independent of elbow rep segmentation."""

from collections.abc import Sequence
from statistics import median

from app.analysis.angle_segmentation import AngleCycleConfig
from app.analysis.geometry import measure_joint_angle
from app.domain.analysis import RepAnalysis
from app.domain.pose import PoseFrame

MAX_BODY_LINE_GAP_MS = AngleCycleConfig().maximum_gap_ms


def add_body_line_measurements(
    reps: Sequence[RepAnalysis],
    frames: Sequence[PoseFrame],
    *,
    side: str,
    image_width: int,
    image_height: int,
    minimum_visibility: float,
) -> list[RepAnalysis]:
    """Median raw 2D hip-vertex angle over each counted [startMs, endMs] interval.

    Require both boundaries, at least three samples, every angle usable, and no gap
    over the counter's 300 ms limit. Do not fill missing samples or switch sides.
    Each completed rep depends only on its interval, so later frames cannot revise it.
    The median is sample-weighted, not time-weighted, and does not describe peak deviation.
    """
    if not reps:
        return []
    names = tuple(f"{side}_{joint}" for joint in ("shoulder", "hip", "ankle"))
    samples = [
        (
            frame.timestamp_ms,
            measure_joint_angle(
                frame,
                names,
                image_width=image_width,
                image_height=image_height,
                minimum_visibility=minimum_visibility,
            ).angle_deg,
        )
        for frame in frames
    ]
    updated = []
    for original in reps:
        rep = original.model_copy(deep=True)
        window = [(time, angle) for time, angle in samples if rep.start_ms <= time <= rep.end_ms]
        usable = [angle for _, angle in window if angle is not None]
        complete = (
            len(window) >= 3
            and len(usable) == len(window)
            and window[0][0] == rep.start_ms
            and window[-1][0] == rep.end_ms
            and all(
                0 < current[0] - previous[0] <= MAX_BODY_LINE_GAP_MS
                for previous, current in zip(window, window[1:], strict=False)
            )
        )
        rep.measurements.update(
            {
                "bodyLineSampleCount": len(window),
                "bodyLineUsableSampleCount": len(usable),
                f"median{side.title()}ShoulderHipAnkleAngleDeg": median(usable)
                if complete
                else None,
            }
        )
        updated.append(rep)
    return updated
