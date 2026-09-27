"""Human-readable observation coverage; never a camera or form quality score."""

from collections import Counter
from collections.abc import Sequence

from app.analysis.geometry import AngleMeasurement, measure_joint_angle
from app.analysis.visibility import LandmarkProblem, check_landmarks
from app.domain.pose import PoseFrame

REASON_LABELS = {
    "missing": "not detected",
    "out_of_frame": "outside the image",
    "unknown_visibility": "visibility unknown",
    "low_visibility": "low estimated visibility",
}


def _joint_feedback(
    problems: Sequence[Sequence[LandmarkProblem]], names: Sequence[str], total: int
) -> list[str]:
    counts = Counter((problem.name, problem.reason) for frame in problems for problem in frame)
    messages = []
    for name in names:
        blocked = sum(counts[name, reason] for reason in REASON_LABELS)
        if not blocked:
            continue
        reasons = ", ".join(
            f"{counts[name, reason]} {label}"
            for reason, label in REASON_LABELS.items()
            if counts[name, reason]
        )
        if counts[name, "out_of_frame"]:
            cue = "Adjust framing to keep this joint inside the image."
        elif counts[name, "missing"] or counts[name, "low_visibility"]:
            cue = "Keep this joint unobstructed and clearly lit."
        else:
            cue = "Visibility could not be assessed; this joint cannot support a measurement yet."
        messages.append(
            f"{name.replace('_', ' ').capitalize()} unavailable in {blocked} of {total} "
            f"sampled frames ({reasons}). {cue}"
        )
    return messages


def _angle_feedback(
    measurements: Sequence[AngleMeasurement], names: tuple[str, str, str]
) -> list[str]:
    available = sum(value.angle_deg is not None for value in measurements)
    label = names[1].replace("_", " ").capitalize()
    messages = [f"{label} angle available in {available} of {len(measurements)} sampled frames."]
    messages.extend(
        _joint_feedback(
            [value.landmark_problems for value in measurements], names, len(measurements)
        )
    )
    degenerate = sum(value.unavailable_reason == "degenerate_geometry" for value in measurements)
    if degenerate:
        messages.append(
            f"{label} angle undefined in {degenerate} sampled frames because joint positions "
            "coincide. Check the skeleton against the video; no angle was inferred."
        )
    return messages


def tracking_feedback(
    frames: Sequence[PoseFrame],
    *,
    side: str | None,
    joints: tuple[str, str, str],
    image_width: int,
    image_height: int,
    minimum_visibility: float,
    include_body_line: bool = False,
) -> list[str]:
    """Describe the locked side over all received samples, or both sides if none was usable.

    Recheck the selected side even before it locked: the counter's pre-lock failed attempt
    may describe the other side. This report never feeds the counter or changes its side.
    Counts refer to samples, not elapsed-time coverage or current camera readiness.
    """
    if not frames:
        return ["No pose frames received yet; tracking coverage is unknown."]
    messages = []
    for candidate in (side,) if side else ("left", "right"):
        names = tuple(f"{candidate}_{joint}" for joint in joints)
        measurements = [
            measure_joint_angle(
                frame,
                names,
                image_width=image_width,
                image_height=image_height,
                minimum_visibility=minimum_visibility,
            )
            for frame in frames
        ]
        messages.extend(_angle_feedback(measurements, names))

    if include_body_line and side:
        names = tuple(f"{side}_{joint}" for joint in ("shoulder", "hip", "ankle"))
        problems = [
            check_landmarks(frame, names, minimum_visibility=minimum_visibility) for frame in frames
        ]
        available = sum(not problem for problem in problems)
        messages.append(
            f"{side.capitalize()} shoulder, hip and ankle pass landmark visibility checks together "
            f"in {available} of {len(frames)} sampled frames. "
            "Visibility alone does not assess body alignment."
        )
        # Shoulder problems already appear in elbow feedback; do not repeat them.
        messages.extend(_joint_feedback(problems, names[1:], len(frames)))
    return messages
