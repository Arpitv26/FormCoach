import pytest

from app.analysis.visibility import LandmarkProblem, check_landmarks
from app.domain.pose import LANDMARK_NAMES, PoseFrame, PoseLandmark


def make_frame(*landmarks: tuple[str, float, float, float | None]) -> PoseFrame:
    return PoseFrame(
        frame_index=0,
        timestamp_ms=0,
        landmarks=[
            PoseLandmark(
                index=LANDMARK_NAMES.index(name), name=name, x=x, y=y, visibility=visibility
            )
            for name, x, y, visibility in landmarks
        ],
    )


def test_missing_joints_are_reported_by_name_in_requested_order():
    frame = make_frame(("left_hip", 0.5, 0.3, 0.9))
    assert check_landmarks(
        frame, ("left_ankle", "left_hip", "left_knee"), minimum_visibility=0.7
    ) == (LandmarkProblem("left_ankle", "missing"), LandmarkProblem("left_knee", "missing"))


@pytest.mark.parametrize(
    ("visibility", "threshold", "reason"),
    [
        (None, 0.7, "unknown_visibility"),
        (0.69, 0.7, "low_visibility"),
        (0, 0.7, "low_visibility"),
        (None, 0, "unknown_visibility"),
        (0.7, 0.7, None),
        (0.9, 0.7, None),
        (1, 1, None),
        (0, 0, None),
    ],
)
def test_visibility_is_explicit_and_threshold_is_inclusive(visibility, threshold, reason):
    frame = make_frame(("left_knee", 0.5, 0.5, visibility))
    expected = () if reason is None else (LandmarkProblem("left_knee", reason),)
    assert check_landmarks(frame, ("left_knee",), minimum_visibility=threshold) == expected


@pytest.mark.parametrize(("x", "y"), [(-0.01, 0.5), (1.01, 0.5), (0.5, -0.01), (0.5, 1.01)])
def test_high_visibility_does_not_make_outside_estimates_usable(x, y):
    frame = make_frame(("left_knee", x, y, 1))
    before = frame.model_dump()
    assert check_landmarks(frame, ("left_knee",), minimum_visibility=0.7) == (
        LandmarkProblem("left_knee", "out_of_frame"),
    )
    assert frame.model_dump() == before


@pytest.mark.parametrize(("x", "y"), [(0, 0), (0, 1), (1, 0), (1, 1)])
def test_image_boundary_is_included(x, y):
    frame = make_frame(("left_knee", x, y, 0.9))
    assert check_landmarks(frame, ("left_knee",), minimum_visibility=0.7) == ()


def test_only_requested_joints_are_gated():
    frame = make_frame(("right_knee", 0.5, 0.5, None), ("left_knee", 0.5, 0.5, 0.9))
    assert check_landmarks(frame, ("left_knee",), minimum_visibility=0.7) == ()


def test_outside_takes_precedence_over_unknown_visibility():
    frame = make_frame(("left_knee", -0.1, 0.5, None))
    assert check_landmarks(frame, ("left_knee",), minimum_visibility=0.7) == (
        LandmarkProblem("left_knee", "out_of_frame"),
    )


@pytest.mark.parametrize("threshold", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_visibility_configuration_is_rejected(threshold):
    with pytest.raises(ValueError, match="minimum_visibility"):
        check_landmarks(make_frame(), ("left_knee",), minimum_visibility=threshold)


@pytest.mark.parametrize("names", [(), ("knee_left",), ("left_knee", "left_knee")])
def test_bad_landmark_configuration_is_not_reported_as_camera_failure(names):
    with pytest.raises(ValueError):
        check_landmarks(make_frame(), names, minimum_visibility=0.7)
