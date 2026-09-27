"""Known geometry and strict coverage; no trained form labels or quality thresholds."""

from copy import deepcopy
from math import cos, radians, sin

import pytest
from test_lat_pulldown import lat_request
from test_live_analysis import analyze

from app.analysis.exercises.gym_torso import add_torso_measurements, torso_angle
from app.domain.models import CoachRequest
from app.domain.pose import LANDMARK_NAMES, LiveBatchRequest
from app.services.coach_evidence import evidence_cards
from app.services.conversation_coach import local_reply


def torso_request(side="left"):
    request = lat_request(side=side, final=True)
    for i, frame in enumerate(request["frames"]):
        shoulder = next(p for p in frame["landmarks"] if p["name"] == f"{side}_shoulder")
        angle = 35 if i == 12 else 5
        name = f"{side}_hip"
        frame["landmarks"].append(
            dict(
                name=name,
                index=LANDMARK_NAMES.index(name),
                visibility=0.9,
                x=shoulder["x"] - 150 * sin(radians(angle)) / request["imageWidth"],
                y=shoulder["y"] + 150 * cos(radians(angle)) / request["imageHeight"],
            )
        )
    return request


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize(
    "width,height,mirror", [(1280, 720, False), (720, 1280, False), (1280, 720, True)]
)
def test_known_geometry_marker_coach_and_unchanged_counts(client, side, width, height, mirror):
    request = torso_request(side)
    for f in request["frames"]:
        for p in f["landmarks"]:
            p["x"] *= 0.5 * 1280 / width
            p["y"] *= 0.5 * 720 / height
            if mirror:
                p["x"] = 1 - p["x"]
    request.update(imageWidth=width, imageHeight=height)
    result = analyze(client, request)
    rep = result.reps[0]
    assert rep.measurements[f"min{side.title()}TorsoTiltDeg"] == pytest.approx(5)
    assert rep.measurements[f"max{side.title()}TorsoTiltDeg"] == pytest.approx(35)
    assert rep.measurements[f"{side}TorsoTiltRangeDeg"] == pytest.approx(30)
    moment = next(m for m in rep.key_moments if m.type == "maximum_torso_tilt")
    assert moment.timestamp_ms == request["frames"][12]["timestampMs"]
    assert result.summary.total_reps == 3 and not result.issues and rep.score is None
    card = next(c for c in evidence_cards(result) if c.id == f"rep-1-{side}-torso")
    assert "30.0° range" in card.text and "not a diagnosis" in card.text
    reply = local_reply(CoachRequest(analysis=result, mode="summary"))
    assert "30.0°" in reply.message and "not a form grade" in reply.message
    assert all("torso" not in c.id for c in evidence_cards(analyze(client, lat_request())))


@pytest.mark.parametrize("failure", ["missing", "unknown", "low", "outside", "degenerate"])
def test_unusable_hip_nulls_interval_without_changing_elbow_count(client, failure):
    request = torso_request()
    baseline = analyze(client, request)
    point = request["frames"][12]["landmarks"][-1]
    if failure == "missing":
        request["frames"][12]["landmarks"].remove(point)
    elif failure == "unknown":
        point["visibility"] = None
    elif failure == "low":
        point["visibility"] = 0.69
    elif failure == "outside":
        point["x"] = -0.1
    else:
        shoulder = request["frames"][12]["landmarks"][0]
        point.update(x=shoulder["x"], y=shoulder["y"])
    result = analyze(client, request)
    assert result.summary == baseline.summary and result.timeline == baseline.timeline
    assert result.reps[0].measurements["leftTorsoTiltRangeDeg"] is None
    assert result.reps[1].measurements["leftTorsoTiltRangeDeg"] == pytest.approx(0)
    assert not any(c.id == "rep-1-left-torso" for c in evidence_cards(result))
    assert not any(m.type == "maximum_torso_tilt" for m in result.reps[0].key_moments)


@pytest.mark.parametrize("failure", ["start", "end", "gap", "short"])
def test_missing_boundaries_and_internal_gap_are_unknown(client, failure):
    b = LiveBatchRequest.model_validate(torso_request())
    rep = analyze(client, torso_request()).reps[0]
    frames = [f for f in b.frames if rep.start_ms <= f.timestamp_ms <= rep.end_ms]
    if failure == "start":
        frames = frames[1:]
    elif failure == "end":
        frames = frames[:-1]
    elif failure == "gap":
        frames = frames[:2] + frames[6:]
    else:
        frames = [frames[0], frames[-1]]
    updated = add_torso_measurements(
        [rep], frames, side="left", image_width=1280, image_height=720, minimum_visibility=0.7
    )
    assert updated[0].measurements["leftTorsoTiltRangeDeg"] is None


def test_completed_measurements_causal_no_mutation(client):
    request = torso_request()
    original = deepcopy(request)
    previous = []
    for end in range(1, len(request["frames"]) + 1):
        result = analyze(client, {**request, "frames": request["frames"][:end], "isFinal": False})
        assert result.reps[: len(previous)] == previous
        previous = result.reps
    assert request == original


@pytest.mark.parametrize(
    "key,value",
    [
        ("torsoUsableSampleCount", 0),
        ("torsoSampleCount", 2.5),
        ("leftTorsoTiltRangeDeg", 999),
        ("maxLeftTorsoTiltDeg", None),
    ],
)
def test_coach_rejects_inconsistent_metadata(client, key, value):
    result = analyze(client, torso_request())
    result.reps[0].measurements[key] = value
    assert not any(c.id == "rep-1-left-torso" for c in evidence_cards(result))


def test_zero_angle_is_valid_not_unknown():
    b = LiveBatchRequest.model_validate(torso_request())
    frame = b.frames[0].model_copy(deep=True)
    shoulder, hip = frame.landmarks[0], frame.landmarks[-1]
    hip.x = shoulder.x
    assert (
        torso_angle(frame, side="left", image_width=1280, image_height=720, minimum_visibility=0.7)
        == 0
    )
