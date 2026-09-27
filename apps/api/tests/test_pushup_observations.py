"""Independent interval geometry, absence of invented reps, and coach grounding."""

from copy import deepcopy
from math import cos, radians, sin

import pytest
from pydantic import ValidationError
from test_live_analysis import analyze
from test_pushup_analysis import pushup_request

from app.domain.analysis import AnalysisResponse
from app.domain.models import CoachRequest
from app.domain.pose import LANDMARK_NAMES
from app.services.coach_evidence import evidence_cards
from app.services.conversation_coach import local_reply


def observation_request(body_angles=None, *, side="left", final=True):
    angles = body_angles if body_angles is not None else [130] * 11
    request = pushup_request([170] * len(angles), side=side, final=final)
    for frame, angle in zip(request["frames"], angles, strict=True):
        # Shoulder at (500,200), hip at (650,200); known angle at the hip.
        for joint, x, y in (
            ("hip", 650, 200),
            ("ankle", 650 + 150 * cos(radians(180 - angle)), 200 + 150 * sin(radians(180 - angle))),
        ):
            name = f"{side}_{joint}"
            frame["landmarks"].append(
                dict(
                    index=LANDMARK_NAMES.index(name),
                    name=name,
                    x=x / 1280,
                    y=y / 720,
                    visibility=0.9,
                )
            )
    return request


@pytest.mark.parametrize("side", ["left", "right"])
def test_visible_bend_without_reps_has_timestamps_and_evidence(client, side):
    result = analyze(client, observation_request(side=side))
    assert result.summary.total_reps == 0
    assert result.reps == [] and result.issues == [] and result.summary.overall_score is None
    [item] = result.movement_observations
    assert (item.start_ms, item.end_ms, item.sample_count, item.side) == (0, 1000, 11, side)
    assert item.median_angle_deg == pytest.approx(130)
    assert item.min_angle_deg == pytest.approx(130)
    assert item.max_angle_deg == pytest.approx(130)
    cards = evidence_cards(result)
    assert cards[0].id == "movement-1-body-line"
    data = result.model_dump(by_alias=True)
    for path in cards[0].paths:
        value = data
        for key in path.split("."):
            value = value[int(key)] if isinstance(value, list) else value[key]
        assert value is not None
    reply = local_reply(
        CoachRequest(analysis=result, mode="summary", response_style="conversation")
    )
    assert "noticeable bend" in reply.message and reply.provider == "fallback"
    assert "movementObservations.0.medianAngleDeg" in reply.evidence
    dispute = local_reply(
        CoachRequest(
            analysis=result,
            mode="qa",
            question="You missed my reps.",
            response_style="conversation",
        )
    )
    assert "bend" in dispute.message and "why a rep did not count" in dispute.message
    assert "movementObservations.0.medianAngleDeg" in dispute.evidence


@pytest.mark.parametrize(
    "angles", [[180] * 11, [150] * 11, [149] * 5, [180] * 5 + [100] + [180] * 5]
)
def test_straight_boundary_short_run_and_single_spike_are_not_flagged(client, angles):
    assert not analyze(client, observation_request(angles)).movement_observations


@pytest.mark.parametrize("failure", ["visibility", "missing", "outside", "gap", "vertical"])
def test_lost_or_ineligible_geometry_does_not_bridge_short_runs(client, failure):
    request = observation_request()
    if failure == "gap":
        for frame in request["frames"][5:]:
            frame["timestampMs"] += 301
        request["frames"] = request["frames"][:10]
    elif failure == "vertical":
        # Rotate all points 90 degrees in pixel space; preserves angle, excludes upright setup.
        for frame in request["frames"]:
            for point in frame["landmarks"]:
                x, y = point["x"] * 1280, point["y"] * 720
                point["x"], point["y"] = y / 1280, (x - 300) / 720
    else:
        hip = request["frames"][5]["landmarks"][-2]
        if failure == "visibility":
            hip["visibility"] = None
        elif failure == "outside":
            hip["y"] = -0.1
        else:
            request["frames"][5]["landmarks"].remove(hip)
    assert not analyze(client, request).movement_observations


def test_completed_intervals_are_stable_and_open_live_interval_waits(client):
    request = observation_request([130] * 11 + [180] + [130] * 11, final=False)
    before = deepcopy(request)
    assert not analyze(client, {**request, "frames": request["frames"][:11]}).movement_observations
    first = analyze(client, {**request, "frames": request["frames"][:12]})
    full = analyze(client, request)
    assert full.movement_observations == first.movement_observations
    final = analyze(client, {**request, "isFinal": True})
    assert final.movement_observations[:1] == first.movement_observations
    assert len(final.movement_observations) == 2
    assert request == before


def test_aspect_ratio_mirror_and_side_lock(client):
    request = observation_request()
    baseline = analyze(client, request).movement_observations
    for frame in request["frames"]:
        for point in frame["landmarks"]:
            point["x"] = 1 - point["x"] * 0.5 * 1280 / 720
            point["y"] *= 0.5 * 720 / 1280
    request.update(imageWidth=720, imageHeight=1280)
    assert analyze(client, request).movement_observations[0].median_angle_deg == pytest.approx(
        baseline[0].median_angle_deg
    )
    request = observation_request()
    other = observation_request(side="right")
    for left, right in zip(request["frames"], other["frames"], strict=True):
        left["landmarks"].extend(right["landmarks"])
        left["landmarks"][3]["visibility"] = 0
    assert not analyze(
        client, request
    ).movement_observations  # Cannot switch to visible right body.


@pytest.mark.parametrize(
    "field,value",
    [
        ("endMs", 499),
        ("sampleCount", 2),
        ("medianAngleDeg", 151),
        ("minAngleDeg", 140),
        ("thresholdAngleDeg", 160),
    ],
)
def test_inconsistent_interval_evidence_is_rejected(client, field, value):
    data = analyze(client, observation_request()).model_dump(by_alias=True)
    data["movementObservations"][0][field] = value
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(data)


def test_legacy_response_and_session_bounds(client):
    data = analyze(client, observation_request()).model_dump(by_alias=True)
    data["source"]["durationMs"] = 900
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(data)
    data["source"]["durationMs"] = 1000
    del data["movementObservations"]
    assert AnalysisResponse.model_validate(data).movement_observations == []
