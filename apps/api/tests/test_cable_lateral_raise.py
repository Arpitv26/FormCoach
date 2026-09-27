"""Known synthetic shoulder angles, single-arm visibility and lift completion."""

import pytest
from test_live_analysis import analyze, squat_request

from app.analysis.rising_segmentation import RisingConfig
from app.domain.models import CoachRequest
from app.services.coach_evidence import evidence_cards
from app.services.conversation_coach import local_reply

LOW = [15] * 5
LIFT = [45] * 4 + [80] * 4


def raise_request(angles=None, *, side="left", final=True):
    request = squat_request((LOW + LIFT) * 7 if angles is None else angles, side=side, final=final)
    request["exerciseHint"] = "cable-lateral-raise"
    for frame in request["frames"]:
        for point, (name, index) in zip(
            frame["landmarks"], [("hip", 23), ("shoulder", 11), ("elbow", 13)], strict=True
        ):
            point["name"] = f"{side}_{name}"
            point["index"] = index + (side == "right")
    return request


@pytest.mark.parametrize("side", ["left", "right"])
def test_counts_lifts_and_uses_shoulder_geometry_not_elbow(client, side):
    result = analyze(client, raise_request(side=side))
    assert result.summary.total_reps == 7 and result.status == "complete"
    assert result.exercise.id == "cable-lateral-raise"
    rep = result.reps[-1]
    assert rep.measurements[f"minSmoothed{side.title()}ShoulderAngleDeg"] == pytest.approx(15)
    assert rep.measurements[f"maxSmoothed{side.title()}ShoulderAngleDeg"] == pytest.approx(80)
    assert all("Elbow" not in key for key in rep.measurements)
    assert rep.key_moments[-1].type == "raised_position"
    assert rep.score is None and not result.issues and not result.movement_observations
    cards = evidence_cards(result, preferred_reps=(7,))
    assert any("shoulder excursion" in c.text and "Rep 7" in c.text for c in cards)
    assert not any("elbow excursion" in c.text for c in cards)
    assert "push-up" not in local_reply(CoachRequest(analysis=result, mode="summary")).message


@pytest.mark.parametrize(
    "angles,count",
    [
        ([], None),
        ([80] * 30, None),
        (LOW, 0),
        (LOW + [45] * 12, 0),
        (LOW + [45] * 4 + [80] + [45] * 4, 0),
        (LOW + LIFT + [80] * 40, 1),
        (LOW + LIFT + [45] * 10 + LIFT, 1),
    ],
)
def test_unready_static_partial_and_spikes(client, angles, count):
    assert analyze(client, raise_request(angles)).summary.total_reps == count


def test_dropout_after_completed_lift_keeps_it_but_during_lift_does_not(client):
    request = raise_request((LOW + LIFT) * 2)
    # First lift already complete; second arm motion is lost before its high zone.
    request["frames"][12]["landmarks"] = []
    request["frames"][20]["landmarks"] = []
    result = analyze(client, request)
    assert result.summary.total_reps == 1 and result.status == "partial"


def test_finalization_does_not_count_a_partial_lift_and_prefixes_stay_stable(client):
    request = raise_request((LOW + LIFT) * 3 + LOW + [45] * 6)
    previous = []
    for end in range(1, len(request["frames"]) + 1):
        result = analyze(client, {**request, "frames": request["frames"][:end], "isFinal": False})
        assert result.reps[: len(previous)] == previous
        previous = result.reps
    final = analyze(client, request)
    assert final.reps == previous and final.summary.total_reps == 3


@pytest.mark.parametrize(
    "changes",
    [
        {"ready_angle_deg": float("nan")},
        {"target_angle_deg": 181},
        {"target_angle_deg": 35},
        {"minimum_phase_ms": 0},
        {"maximum_rep_ms": 200},
        {"maximum_gap_ms": 3.2},
    ],
)
def test_invalid_rising_configuration_is_rejected(changes):
    with pytest.raises(ValueError):
        RisingConfig(**{"ready_angle_deg": 30, "target_angle_deg": 60, **changes})
