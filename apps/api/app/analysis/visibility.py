"""Gate measurements on named domain landmarks, not provider-specific objects."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Literal

from app.domain.pose import LANDMARK_NAMES, PoseFrame


@dataclass(frozen=True)
class LandmarkProblem:
    name: str
    reason: Literal["missing", "out_of_frame", "unknown_visibility", "low_visibility"]


def check_landmarks(
    frame: PoseFrame,
    required_names: Sequence[str],
    *,
    minimum_visibility: float,
) -> tuple[LandmarkProblem, ...]:
    """Return one problem per unusable joint, in the caller's requested order.

    An empty result means these joints pass this gate, not that the camera view or
    movement is suitable. The caller supplies the exercise's visibility heuristic.
    Coordinates on the image boundary are accepted; outside estimates are never clamped.
    Missing/outside takes precedence over unknown/low visibility for the same joint.
    """
    if not isfinite(minimum_visibility) or not 0 <= minimum_visibility <= 1:
        raise ValueError("minimum_visibility must be finite and between 0 and 1")
    if not required_names or len(set(required_names)) != len(required_names):
        raise ValueError("Required landmark names must be non-empty and unique")
    if any(name not in LANDMARK_NAMES for name in required_names):
        raise ValueError("Use canonical landmark names from the pose contract")

    by_name = {landmark.name: landmark for landmark in frame.landmarks}
    problems: list[LandmarkProblem] = []
    for name in required_names:
        landmark = by_name.get(name)
        if landmark is None:
            problems.append(LandmarkProblem(name, "missing"))
        elif not (0 <= landmark.x <= 1 and 0 <= landmark.y <= 1):
            problems.append(LandmarkProblem(name, "out_of_frame"))
        elif landmark.visibility is None:
            problems.append(LandmarkProblem(name, "unknown_visibility"))
        elif landmark.visibility < minimum_visibility:
            problems.append(LandmarkProblem(name, "low_visibility"))
    return tuple(problems)
