from math import sqrt

import pytest

from app.analysis.exercises.squat import SQUAT_PROFILE
from app.analysis.geometry import angle_degrees, measure_joint_angle
from app.domain.pose import LANDMARK_NAMES, PoseFrame, PoseLandmark

LEFT_KNEE = ("left_hip", "left_knee", "left_ankle")


@pytest.mark.parametrize(
    ("start", "vertex", "end", "expected"),
    [
        ((1, 0), (0, 0), (0, 1), 90),
        ((-1, 0), (0, 0), (1, 0), 180),
        ((1, 0), (0, 0), (1, 1), 45),
        ((1, 0), (0, 0), (-1, sqrt(3)), 120),
        ((1, 0), (0, 0), (2, 0), 0),
    ],
)
def test_known_interior_angles(start, vertex, end, expected):
    assert angle_degrees(start, vertex, end) == pytest.approx(expected)
    assert angle_degrees(end, vertex, start) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("start", "vertex", "end"),
    [
        ((0, 0), (0, 0), (1, 1)),
        ((1, 1), (0, 0), (0, 0)),
        ((0, 0), (0, 0), (0, 0)),
        ((float("nan"), 0), (0, 0), (1, 1)),
        ((1, 0), (float("inf"), 0), (0, 1)),
        ((1, 0), (0, 0), (0, -float("inf"))),
        ((1e308, 0), (-1e308, 0), (0, 1)),
    ],
)
def test_undefined_geometry_is_unknown(start, vertex, end):
    assert angle_degrees(start, vertex, end) is None


def test_angle_is_stable_near_straight_and_at_small_scales():
    assert angle_degrees((-1, 1e-12), (0, 0), (1, 0)) == pytest.approx(180)
    assert angle_degrees((1e-150, 0), (0, 0), (0, 1e-150)) == pytest.approx(90)


def knee_frame(width=1280, height=720, names=LEFT_KNEE):
    """A known pixel-space right angle with two diagonal arms, not axis-aligned arms."""
    center_x, center_y = width / 2, height / 2
    points = [
        (center_x + 100, center_y - 100),
        (center_x, center_y),
        (center_x + 100, center_y + 100),
    ]
    return PoseFrame(
        frame_index=12,
        timestamp_ms=800,
        landmarks=[
            PoseLandmark(
                index=LANDMARK_NAMES.index(name),
                name=name,
                x=x / width,
                y=y / height,
                visibility=0.9,
            )
            for name, (x, y) in zip(names, points, strict=True)
        ],
    )


def measure_knee(frame, width=1280, height=720, names=LEFT_KNEE):
    return measure_joint_angle(
        frame,
        names,
        image_width=width,
        image_height=height,
        minimum_visibility=SQUAT_PROFILE.minimum_visibility,
    )


@pytest.mark.parametrize(("width", "height"), [(640, 480), (1920, 1080), (720, 1280), (640, 640)])
def test_normalized_coordinates_recover_pixel_angle_at_every_aspect_ratio(width, height):
    frame = knee_frame(width, height)
    before = frame.model_dump()
    result = measure_knee(frame, width, height)
    assert result.angle_deg == pytest.approx(90)
    assert result.unavailable_reason is None
    assert result.landmark_problems == ()
    assert frame.model_dump() == before


def test_measurement_uses_names_not_list_positions_or_the_other_side():
    right_names = ("right_hip", "right_knee", "right_ankle")
    frame = knee_frame(names=right_names)
    frame.landmarks.reverse()
    assert measure_knee(frame, names=right_names).angle_deg == pytest.approx(90)
    left = measure_knee(frame)
    assert left.angle_deg is None
    assert [problem.name for problem in left.landmark_problems] == list(LEFT_KNEE)


@pytest.mark.parametrize("mutation", ["missing", "unknown", "low", "outside"])
def test_any_unusable_required_landmark_blocks_angle(mutation):
    frame = knee_frame()
    if mutation == "missing":
        frame.landmarks.pop(1)
    elif mutation == "unknown":
        frame.landmarks[1].visibility = None
    elif mutation == "low":
        frame.landmarks[1].visibility = 0.2
    else:
        frame.landmarks[1].x = 1.1
    result = measure_knee(frame)
    assert result.angle_deg is None
    assert result.unavailable_reason == "unusable_landmarks"
    assert len(result.landmark_problems) == 1
    assert result.landmark_problems[0].name == "left_knee"


def test_degenerate_pose_does_not_turn_into_a_zero_degree_angle():
    frame = knee_frame()
    frame.landmarks[0].x = frame.landmarks[1].x
    frame.landmarks[0].y = frame.landmarks[1].y
    result = measure_knee(frame)
    assert result.angle_deg is None
    assert result.unavailable_reason == "degenerate_geometry"
    assert result.landmark_problems == ()


def test_relative_depth_is_not_used_for_image_plane_angles():
    frame = knee_frame()
    for landmark, depth in zip(frame.landmarks, (-10, 50, None), strict=True):
        landmark.z = depth
    assert measure_knee(frame).angle_deg == pytest.approx(90)


@pytest.mark.parametrize(
    ("width", "height"), [(0, 720), (-1, 720), (1280, 0), (1.5, 720), (True, 720)]
)
def test_invalid_dimensions_raise_configuration_error(width, height):
    with pytest.raises(ValueError, match="positive integers"):
        measure_knee(knee_frame(), width, height)


@pytest.mark.parametrize(
    "names", [("left_hip", "left_knee"), ("left_hip", "left_knee", "left_knee")]
)
def test_invalid_joint_definition_is_rejected(names):
    with pytest.raises(ValueError):
        measure_knee(knee_frame(), names=names)
