"""HTTP integration with synthetic geometry, not evidence of real-camera accuracy."""

import json
from copy import deepcopy
from math import cos, radians, sin
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from app.domain.analysis import AnalysisResponse

STANDING = [170] * 5
CYCLE = [140] * 5 + [90] * 5 + [130] * 5 + STANDING
ENDPOINT = "/api/v1/live/analyze-batch"


def squat_request(angles=None, *, side="left", final=False):
    """Author pixel geometry with known angles, then normalize to a nonsquare image."""
    if angles is None:
        angles = STANDING + CYCLE
    frames = []
    for index, angle in enumerate(angles):
        points = [
            (23, "hip", 500, 200),
            (25, "knee", 500, 400),
            (27, "ankle", 500 + 200 * sin(radians(angle)), 400 - 200 * cos(radians(angle))),
        ]
        frames.append(
            {
                "frameIndex": index,
                "timestampMs": index * 100,
                "landmarks": [
                    {
                        "index": joint_index + (side == "right"),
                        "name": f"{side}_{joint}",
                        "x": x / 1280,
                        "y": y / 720,
                        "visibility": 0.9,
                    }
                    for joint_index, joint, x, y in points
                ],
            }
        )
    return {
        "contractVersion": "1.0",
        "sessionId": "synthetic-http-test",
        "exerciseHint": "squat",
        "imageWidth": 1280,
        "imageHeight": 720,
        "isFinal": final,
        "frames": frames,
    }


def analyze(client, request):
    response = client.post(ENDPOINT, json=request)
    assert response.status_code == 200, response.text
    return AnalysisResponse.model_validate(response.json())


@pytest.mark.parametrize("side", ["left", "right"])
def test_measures_completed_rep_and_preserves_v1_schema(client, side):
    result = analyze(client, squat_request(side=side, final=True))
    assert result.contract_version == "1.0"
    assert result.status == "complete"
    assert result.provenance.kind == "measured"
    assert result.source.duration_ms == 2400
    assert result.exercise.id == "squat"
    assert result.exercise.confidence is None
    assert result.summary.total_reps == 1
    rep = result.reps[0]
    assert (rep.start_ms, rep.end_ms) == (600, 2300)
    assert rep.measurements == {
        f"minSmoothed{side.title()}KneeAngleDeg": pytest.approx(90),
        "durationMs": 1700,
    }
    assert rep.key_moments[0].timestamp_ms == 1100
    assert [(event.type, event.timestamp_ms) for event in result.timeline] == [
        ("rep_start", 600),
        ("key_moment", 1100),
        ("rep_end", 2300),
    ]
    assert all(event.rep_number == 1 and event.issue_id is None for event in result.timeline)
    assert result.summary.overall_score is None
    assert result.summary.primary_focus is None
    assert result.scoring is None and rep.score is None
    assert all(value is None for value in result.metrics.model_dump().values())
    assert all(value is None for value in rep.metrics.model_dump().values())
    assert result.camera_quality.score is None and result.camera_quality.full_body_visible is None
    assert not result.issues and not rep.issues
    root = Path(__file__).resolve().parents[3]
    schema = json.loads((root / "contracts/analysis.schema.json").read_text())
    Draft202012Validator(schema).validate(result.model_dump(by_alias=True))


def test_cumulative_snapshots_replace_counts_and_do_not_share_session_state(client):
    request = squat_request(STANDING + CYCLE * 6)
    original = deepcopy(request)
    for count in range(1, 7):
        snapshot = {**request, "frames": request["frames"][: 5 + 20 * count]}
        result = analyze(client, snapshot)
        assert result.status == "partial"
        assert result.summary.total_reps == count
        assert [rep.rep_number for rep in result.reps] == list(range(1, count + 1))
        assert analyze(client, snapshot) == result
    assert request == original
    assert analyze(client, squat_request(STANDING)).summary.total_reps == 0
    assert analyze(client, {**request, "sessionId": "another-set"}).summary.total_reps == 6


@pytest.mark.parametrize("angles", [[], [170] * 2, [90] * 20])
def test_unready_is_unknown_not_zero_even_when_final(client, angles):
    result = analyze(client, squat_request(angles, final=True))
    assert result.status == "insufficient_data"
    assert result.summary.total_reps is None
    assert not result.reps and not result.timeline
    assert result.limitations


def test_stable_standing_establishes_zero_and_final_does_not_finish_a_rep(client):
    result = analyze(client, squat_request(STANDING, final=True))
    assert result.status == "complete"
    assert result.summary.total_reps == 0
    result = analyze(client, squat_request(STANDING + CYCLE[:15], final=True))
    assert result.status == "partial"
    assert result.summary.total_reps == 0
    assert any("unfinished repetition" in message for message in result.limitations)


@pytest.mark.parametrize("failure", ["missing", "low", "unknown", "outside", "coincident", "gap"])
def test_broken_tracking_discards_unfinished_rep_but_keeps_completed_reps(client, failure):
    request = squat_request(STANDING + CYCLE * 2, final=True)
    frame = request["frames"][33]
    if failure == "missing":
        frame["landmarks"] = []
    elif failure == "low":
        frame["landmarks"][1]["visibility"] = 0.69
    elif failure == "unknown":
        frame["landmarks"][1]["visibility"] = None
    elif failure == "outside":
        frame["landmarks"][1]["x"] = 1.01
    elif failure == "coincident":
        frame["landmarks"][0]["y"] = frame["landmarks"][1]["y"]
    else:
        for later in request["frames"][33:]:
            later["timestampMs"] += 301
    result = analyze(client, request)
    assert result.status == "partial"
    assert result.summary.total_reps == 1
    assert any("Incomplete tracking" in message for message in result.limitations)
    assert result.reps == analyze(client, squat_request()).reps


def test_tracking_loss_at_end_keeps_completed_count(client):
    request = squat_request(final=True)
    request["frames"][-1]["landmarks"] = []
    result = analyze(client, request)
    assert result.status == "partial"
    assert result.summary.total_reps == 1


def test_no_visible_leg_never_claims_zero_reps_or_camera_readiness(client):
    request = squat_request(final=True)
    for frame in request["frames"]:
        frame["landmarks"] = []
    result = analyze(client, request)
    assert result.status == "insufficient_data"
    assert result.summary.total_reps is None
    assert result.camera_quality.full_body_visible is None
    assert any("No usable" in message for message in result.camera_quality.issues)


def test_recovers_after_initial_missing_pose_but_reports_incomplete_coverage(client):
    request = squat_request([170] * 3 + STANDING + CYCLE, final=True)
    for frame in request["frames"][:3]:
        frame["landmarks"] = []
    result = analyze(client, request)
    assert result.status == "partial"
    assert result.summary.total_reps == 1
    assert result.reps[0].start_ms == 900
    assert any("Incomplete tracking" in message for message in result.limitations)


def test_does_not_switch_knees_to_bridge_occlusion(client):
    left = squat_request()
    right = squat_request(side="right")
    request = deepcopy(left)
    for index, frame in enumerate(request["frames"]):
        frame["landmarks"].extend(right["frames"][index]["landmarks"])
    assert analyze(client, request).reps == analyze(client, left).reps  # Left wins tie.
    request["frames"][13]["landmarks"] = right["frames"][13]["landmarks"]
    result = analyze(client, request)
    assert result.summary.total_reps == 0
    assert any("Uses the left knee" in message for message in result.limitations)


def test_first_usable_side_stays_locked_as_more_frames_arrive(client):
    request = squat_request(side="right")
    left = squat_request()
    for index, frame in enumerate(request["frames"][5:], 5):
        frame["landmarks"].extend(left["frames"][index]["landmarks"])
    result = analyze(client, request)
    assert "minSmoothedRightKneeAngleDeg" in result.reps[0].measurements
    assert any("Uses the right knee" in message for message in result.limitations)


@pytest.mark.parametrize(
    "hint", [None, "push-up", "lunge", "barbell-squat", "bicep-curl", "shoulder-press", "deadlift"]
)
def test_unimplemented_exercises_never_get_squat_results(client, hint):
    request = {**squat_request(), "exerciseHint": hint}
    result = analyze(client, request)
    assert result.status == "not_implemented"
    assert result.provenance.kind == "placeholder"
    assert result.summary.total_reps is None
    assert not result.reps
    assert result.exercise is None if hint is None else result.exercise.id == hint


def test_coach_accepts_real_rep_results_without_inventing_a_score(client):
    result = analyze(client, squat_request(final=True))
    response = client.post(
        "/api/v1/coach", json={"analysis": result.model_dump(by_alias=True), "mode": "summary"}
    )
    assert response.status_code == 200
    assert response.json()["provider"] == "fallback"
    assert response.json()["evidence"] == []
    assert "does not contain an overall score" in response.json()["message"]
