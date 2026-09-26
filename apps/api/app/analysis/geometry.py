"""Image-plane joint angles. These measurements do not establish 3D form or camera readiness."""

from dataclasses import dataclass
from math import atan2, degrees, hypot, isfinite
from typing import Literal

from app.analysis.visibility import LandmarkProblem, check_landmarks
from app.domain.pose import PoseFrame

type Point2D = tuple[float, float]


def angle_degrees(start: Point2D, vertex: Point2D, end: Point2D) -> float | None:
    """Return the unsigned interior angle at vertex, in [0, 180] degrees.

    Both axes must already use the same scale (for example pixels). Coincident points
    with a zero-length arm, non-finite inputs, or overflow produce None, never a fake 0.
    A real zero-degree angle is valid when two nonzero arms point in the same direction.
    """
    if not all(isfinite(value) for point in (start, vertex, end) for value in point):
        return None
    first = (start[0] - vertex[0], start[1] - vertex[1])
    second = (end[0] - vertex[0], end[1] - vertex[1])
    first_length, second_length = hypot(*first), hypot(*second)
    if any(length == 0 or not isfinite(length) for length in (first_length, second_length)):
        return None

    # Unit vectors avoid multiplying large pixel coordinates or dividing tiny products.
    ux, uy = first[0] / first_length, first[1] / first_length
    vx, vy = second[0] / second_length, second[1] / second_length
    return degrees(atan2(abs(ux * vy - uy * vx), ux * vx + uy * vy))


@dataclass(frozen=True)
class AngleMeasurement:
    """Internal result; not a new API contract or a calibrated confidence estimate."""

    angle_deg: float | None
    unavailable_reason: Literal["unusable_landmarks", "degenerate_geometry"] | None = None
    landmark_problems: tuple[LandmarkProblem, ...] = ()


def measure_joint_angle(
    frame: PoseFrame,
    landmark_names: tuple[str, str, str],
    *,
    image_width: int,
    image_height: int,
    minimum_visibility: float,
) -> AngleMeasurement:
    """Measure start -> vertex -> end after visibility and image-bound checks.

    The middle name is the measured joint. Depth z is intentionally unused. Unknown
    or low visibility prevents measurement; passing visibility cannot validate camera
    orientation. Invalid configuration raises ValueError; unavailable pose data returns
    a null measurement and a reason. Inputs are never mutated.
    """
    if any(type(size) is not int or size <= 0 for size in (image_width, image_height)):
        raise ValueError("Image dimensions must be positive integers")
    if len(landmark_names) != 3:
        raise ValueError("A joint angle requires exactly three distinct landmark names")

    problems = check_landmarks(frame, landmark_names, minimum_visibility=minimum_visibility)
    if problems:
        return AngleMeasurement(None, "unusable_landmarks", problems)

    by_name = {landmark.name: landmark for landmark in frame.landmarks}
    # Undo separate x/y normalization before measuring an angle in a non-square image.
    points = tuple(
        (by_name[name].x * image_width, by_name[name].y * image_height) for name in landmark_names
    )
    angle = angle_degrees(*points)
    if angle is None:
        return AngleMeasurement(None, "degenerate_geometry")
    return AngleMeasurement(angle)
