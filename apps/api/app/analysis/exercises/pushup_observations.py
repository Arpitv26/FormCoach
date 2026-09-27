"""Sustained visible body-line bends, including intervals with no completed reps.

This is a 2D geometry review heuristic, not exercise recognition or a form grade.
"""

from collections.abc import Sequence
from statistics import median

from app.analysis.geometry import measure_joint_angle
from app.domain.analysis import MovementObservation
from app.domain.pose import PoseFrame


def observe_body_line(
    frames: Sequence[PoseFrame],
    *,
    side: str,
    image_width: int,
    image_height: int,
    minimum_visibility: float,
    is_final: bool,
) -> list[MovementObservation]:
    """Require continuous usable samples <150° for >=500 ms; never bridge gaps.

    Shoulder-to-ankle direction must be predominantly horizontal in image pixels. This
    excludes common upright setup, but cannot establish the exercise or camera angle.
    Non-final batches emit only closed intervals so later samples cannot revise them.
    """
    observations = []
    run: list[tuple[int, float]] = []

    def finish() -> None:
        if len(run) >= 3 and run[-1][0] - run[0][0] >= 500:
            angles = [angle for _, angle in run]
            observations.append(
                MovementObservation(
                    code="PUSHUP_BODY_LINE_BEND",
                    rule_version="1.0",
                    side=side,
                    start_ms=run[0][0],
                    end_ms=run[-1][0],
                    sample_count=len(run),
                    min_angle_deg=min(angles),
                    median_angle_deg=median(angles),
                    max_angle_deg=max(angles),
                    threshold_angle_deg=150,
                )
            )
        run.clear()

    for frame in frames:
        angle = measure_joint_angle(
            frame,
            tuple(f"{side}_{joint}" for joint in ("shoulder", "hip", "ankle")),
            image_width=image_width,
            image_height=image_height,
            minimum_visibility=minimum_visibility,
        ).angle_deg
        horizontal = False
        if angle is not None:
            points = {point.name: point for point in frame.landmarks}
            shoulder, ankle = points[f"{side}_shoulder"], points[f"{side}_ankle"]
            dx = abs(shoulder.x - ankle.x) * image_width
            dy = abs(shoulder.y - ankle.y) * image_height
            horizontal = dx > 0 and dx >= dy
        if run and not 0 < frame.timestamp_ms - run[-1][0] <= 300:
            finish()
        if angle is None or angle >= 150 or not horizontal:
            finish()
        else:
            run.append((frame.timestamp_ms, angle))
    if is_final:
        finish()
    return observations
