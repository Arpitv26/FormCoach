"""Descriptive torso inclination to image vertical, with strict interval coverage."""

from collections.abc import Sequence

from app.analysis.geometry import angle_degrees
from app.analysis.visibility import check_landmarks
from app.domain.analysis import KeyMoment, RepAnalysis
from app.domain.pose import PoseFrame


def torso_angle(
    frame: PoseFrame,
    *,
    side: str,
    image_width: int,
    image_height: int,
    minimum_visibility: float,
) -> float | None:
    names = tuple(f"{side}_{joint}" for joint in ("shoulder", "hip"))
    if check_landmarks(frame, names, minimum_visibility=minimum_visibility):
        return None
    landmarks = {point.name: point for point in frame.landmarks}
    shoulder, hip = [
        (landmarks[name].x * image_width, landmarks[name].y * image_height) for name in names
    ]
    return angle_degrees(shoulder, hip, (hip[0], hip[1] - 1))


def add_torso_measurements(
    reps: Sequence[RepAnalysis],
    frames: Sequence[PoseFrame],
    *,
    side: str,
    image_width: int,
    image_height: int,
    minimum_visibility: float,
) -> list[RepAnalysis]:
    """Unsigned raw shoulder-to-hip inclination: 0 upright, 90 horizontal in image.

    Require both boundaries, >=3 samples, no missing sample or gap >300 ms. No
    smoothing, interpolation, side switch, threshold or quality inference. Min/max
    range is not total angular travel; crossing vertical can hide direction changes.
    """
    samples = (
        [
            (
                frame.timestamp_ms,
                torso_angle(
                    frame,
                    side=side,
                    image_width=image_width,
                    image_height=image_height,
                    minimum_visibility=minimum_visibility,
                ),
            )
            for frame in frames
        ]
        if reps
        else []
    )
    updated = []
    for original in reps:
        rep = original.model_copy(deep=True)
        window = [(time, angle) for time, angle in samples if rep.start_ms <= time <= rep.end_ms]
        usable = [(time, angle) for time, angle in window if angle is not None]
        complete = (
            len(window) >= 3
            and len(usable) == len(window)
            and window[0][0] == rep.start_ms
            and window[-1][0] == rep.end_ms
            and all(0 < b[0] - a[0] <= 300 for a, b in zip(window, window[1:], strict=False))
        )
        low = min((angle for _, angle in usable), default=None) if complete else None
        peak = max(usable, key=lambda item: item[1]) if complete else None
        high = peak[1] if peak else None
        rep.measurements.update(
            {
                "torsoSampleCount": len(window),
                "torsoUsableSampleCount": len(usable),
                f"min{side.title()}TorsoTiltDeg": low,
                f"max{side.title()}TorsoTiltDeg": high,
                f"{side}TorsoTiltRangeDeg": high - low if complete else None,
            }
        )
        if peak:
            rep.key_moments.append(
                KeyMoment(
                    timestamp_ms=peak[0],
                    type="maximum_torso_tilt",
                    label="Largest observed torso tilt (2D)",
                )
            )
        updated.append(rep)
    return updated
