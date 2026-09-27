"""Coverage explains observations without changing segmentation or asserting form quality."""

from copy import deepcopy

import pytest
from test_live_analysis import CYCLE, STANDING, analyze, squat_request
from test_pushup_analysis import pushup_request

from app.domain.pose import LANDMARK_NAMES


def messages(result):
    return "\n".join(result.camera_quality.issues)


def add_body_landmarks(request, side="left"):
    for frame in request["frames"]:
        for joint, x in (("hip", 0.6), ("ankle", 0.8)):
            name = f"{side}_{joint}"
            frame["landmarks"].append(
                dict(index=LANDMARK_NAMES.index(name), name=name, x=x, y=0.5, visibility=0.9)
            )


@pytest.mark.parametrize("side", ["left", "right"])
def test_only_locked_side_is_reported_and_body_visibility_does_not_gate_reps(client, side):
    request = pushup_request(side=side, final=True)
    before = deepcopy(request)
    result = analyze(client, request)
    text = messages(result)
    assert f"{side.capitalize()} elbow angle available in 25 of 25 sampled frames" in text
    assert (
        f"{side.capitalize()} hip unavailable in 25 of 25 sampled frames (25 not detected)" in text
    )
    assert "pass landmark visibility checks together in 0 of 25" in text
    other = "Right" if side == "left" else "Left"
    assert other not in text
    assert request == before
    add_body_landmarks(request, side)
    with_body = analyze(client, request)
    for key, value in result.reps[0].measurements.items():
        if key not in {
            "bodyLineUsableSampleCount",
            f"median{side.title()}ShoulderHipAnkleAngleDeg",
        }:
            assert with_body.reps[0].measurements[key] == value
    assert with_body.reps[0].key_moments == result.reps[0].key_moments
    assert with_body.summary == result.summary
    assert with_body.status == result.status == "complete"
    assert "pass landmark visibility checks together in 25 of 25" in messages(with_body)
    assert "Visibility alone does not assess body alignment" in messages(with_body)
    assert with_body.camera_quality.full_body_visible is None
    assert with_body.camera_quality.score is None
    assert with_body.summary.overall_score is None
    assert with_body.issues == []


def test_joint_reasons_are_counted_separately_without_double_counting(client):
    request = pushup_request(final=True)
    # After side selection, four different failures on the same wrist.
    request["frames"][6]["landmarks"].pop()
    request["frames"][7]["landmarks"][2].update(x=1.1, visibility=None)
    request["frames"][8]["landmarks"][2]["visibility"] = None
    request["frames"][9]["landmarks"][2]["visibility"] = 0.69
    result = analyze(client, request)
    text = messages(result)
    assert "Left elbow angle available in 21 of 25 sampled frames" in text
    assert (
        "Left wrist unavailable in 4 of 25 sampled frames (1 not detected, 1 outside the image, "
        "1 visibility unknown, 1 low estimated visibility)" in text
    )
    assert "Adjust framing" in text
    assert result.summary.total_reps == 0  # Lost tracking does not become a completed rep.
    assert result.status == "partial"


def test_unknown_visibility_is_not_blended_into_a_light_or_occlusion_diagnosis(client):
    request = pushup_request()
    request["frames"][-1]["landmarks"][1]["visibility"] = None
    result = analyze(client, request)
    joint_message = next(
        item for item in result.camera_quality.issues if "Left elbow unavailable" in item
    )
    assert "1 visibility unknown" in joint_message
    assert "Visibility could not be assessed" in joint_message
    assert "clearly lit" not in joint_message


def test_degenerate_geometry_is_distinct_from_visibility(client):
    request = pushup_request()
    request["frames"][10]["landmarks"][0]["y"] = request["frames"][10]["landmarks"][1]["y"]
    text = messages(analyze(client, request))
    assert "Left elbow angle available in 24 of 25 sampled frames" in text
    assert "Left elbow angle undefined in 1 sampled frames because joint positions coincide" in text
    assert "Left shoulder unavailable" not in text
    assert "Left elbow unavailable" not in text


def test_no_locked_side_explains_both_candidates_without_claiming_body_coverage(client):
    request = pushup_request(STANDING)
    right = pushup_request(STANDING, side="right")
    for frame, other in zip(request["frames"], right["frames"], strict=True):
        frame["landmarks"][1]["visibility"] = 0.1
        other["landmarks"][2]["x"] = -0.1
        frame["landmarks"].extend(other["landmarks"])
    result = analyze(client, request)
    text = messages(result)
    assert "Left elbow angle available in 0 of 5" in text
    assert "Right elbow angle available in 0 of 5" in text
    assert "Left elbow unavailable in 5 of 5 sampled frames (5 low estimated visibility)" in text
    assert "Right wrist unavailable in 5 of 5 sampled frames (5 outside the image)" in text
    assert "Body alignment" not in text
    assert result.summary.total_reps is None


def test_prelock_failures_are_attributed_to_eventually_selected_side(client):
    request = pushup_request([170] * 3 + STANDING + CYCLE)
    right = pushup_request([170] * 3 + STANDING + CYCLE, side="right")
    for index in range(3):
        request["frames"][index]["landmarks"][1]["visibility"] = None
        right["frames"][index]["landmarks"][2]["x"] = -0.1
        request["frames"][index]["landmarks"].extend(right["frames"][index]["landmarks"])
    result = analyze(client, request)
    text = messages(result)
    assert "Left elbow angle available in 25 of 28" in text
    assert "Left elbow unavailable in 3 of 28 sampled frames (3 visibility unknown)" in text
    assert "Right" not in text
    assert result.summary.total_reps == 1


def test_empty_batch_has_unknown_coverage_instead_of_zero_percent(client):
    result = analyze(client, pushup_request([]))
    text = messages(result)
    assert "No pose frames received yet; tracking coverage is unknown" in text
    assert "0 of 0" not in text
    assert result.summary.total_reps is None


def test_gap_can_break_counting_even_when_all_received_samples_have_angles(client):
    request = pushup_request(STANDING + CYCLE * 2, final=True)
    for frame in request["frames"][33:]:
        frame["timestampMs"] += 301
    result = analyze(client, request)
    assert "Left elbow angle available in 45 of 45" in messages(result)
    assert any("not elapsed time or current readiness" in item for item in result.limitations)
    assert any("1 tracking breaks" in item for item in result.limitations)
    assert result.summary.total_reps == 1
    assert result.status == "partial"


def test_hip_and_ankle_must_be_visible_in_the_same_sample(client):
    request = pushup_request()
    add_body_landmarks(request)
    for index, frame in enumerate(request["frames"]):
        frame["landmarks"][-1 if index % 2 else -2]["visibility"] = 0
    result = analyze(client, request)
    assert "pass landmark visibility checks together in 0 of 25" in messages(result)
    assert result.summary.total_reps == 1


def test_legacy_squat_gets_knee_feedback_without_pushup_body_line(client):
    result = analyze(client, squat_request(final=True))
    assert "Left knee angle available in 25 of 25" in messages(result)
    assert "shoulder" not in messages(result)
    assert result.summary.total_reps == 1
