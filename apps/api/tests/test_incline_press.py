"""Synthetic bent-to-extended press intervals; no pose-model accuracy claim."""

import pytest
from test_live_analysis import analyze
from test_pushup_analysis import pushup_request

from app.analysis.exercises.incline_press import segment_incline_presses
from app.analysis.rep_segmentation import AngleSample
from app.domain.models import CoachRequest
from app.services.coach_evidence import evidence_cards
from app.services.conversation_coach import local_reply

READY = [90] * 5
PRESS = [120] * 4 + [160] * 4


def press_request(angles=None, **kwargs):
    return {
        **pushup_request(READY + PRESS if angles is None else angles, **kwargs),
        "exerciseHint": "incline-dumbbell-bench-press",
    }


@pytest.mark.parametrize("side", ["left", "right"])
def test_press_finishes_at_extension_without_waiting_for_lowering(client, side):
    result = analyze(client, press_request(side=side, final=True))
    assert result.summary.total_reps == 1 and result.status == "complete"
    rep = result.reps[0]
    assert rep.measurements[f"minSmoothed{side.title()}ElbowAngleDeg"] == pytest.approx(90)
    assert rep.measurements[f"maxSmoothed{side.title()}ElbowAngleDeg"] == pytest.approx(160)
    assert rep.key_moments[-1].type == "press_completed"
    assert rep.key_moments[-1].timestamp_ms == rep.end_ms
    assert rep.score is None and result.summary.overall_score is None
    assert not result.movement_observations and not result.issues
    cards = evidence_cards(result)
    assert any("incline dumbbell bench press" in card.text for card in cards)
    assert any(card.id == "rep-1-time" for card in cards)
    assert "push-up" not in local_reply(CoachRequest(analysis=result, mode="summary")).message


@pytest.mark.parametrize(
    "angles, count",
    [
        ([], None),
        ([160] * 20, None),
        (READY, 0),
        (READY + [120] * 20, 0),
        (READY + [120] * 4 + [160] + [120] * 4, 0),
        (READY + PRESS + [160] * 50, 1),
        (READY + PRESS + [120] * 8 + PRESS, 1),
        ((READY + PRESS) * 7, 7),
        (READY + [120] * 70 + [160] * 4, 1),
        (READY + [120] * 8 + READY + PRESS, 1),
    ],
)
def test_ready_partial_spikes_holds_and_rearming(client, angles, count):
    assert analyze(client, press_request(angles, final=True)).summary.total_reps == count


@pytest.mark.parametrize("fps", [10, 15, 30])
def test_time_confirmation_and_cumulative_replay(fps):
    samples = []
    # Repeated continuous bent-to-extended sweeps with a visible bottom turn.
    for i in range(6 * fps + 1):
        time = i / fps
        phase = time % 2
        angle = 80 if phase < 0.4 else min(165, 80 + (phase - 0.4) * 85) if phase < 1.4 else 165
        samples.append(AngleSample(round(time * 1000), angle))
    previous = ()
    for end in range(1, len(samples) + 1):
        result = segment_incline_presses(samples[:end])
        assert result.reps[: len(previous)] == previous
        previous = result.reps
    assert len(previous) == 3


@pytest.mark.parametrize("failure", ["missing", "unknown", "low", "outside", "gap"])
def test_tracking_loss_keeps_completed_presses_and_does_not_bridge_sides(client, failure):
    request = press_request((READY + PRESS) * 2, final=True)
    right = press_request((READY + PRESS) * 2, side="right")
    for frame, other in zip(request["frames"], right["frames"], strict=True):
        frame["landmarks"] += other["landmarks"]
    frame = request["frames"][20]
    if failure == "missing":
        frame["landmarks"] = frame["landmarks"][3:]
    elif failure == "unknown":
        frame["landmarks"][1]["visibility"] = None
    elif failure == "low":
        frame["landmarks"][1]["visibility"] = 0.69
    elif failure == "outside":
        frame["landmarks"][1]["x"] = -0.1
    else:
        for frame in request["frames"][20:]:
            frame["timestampMs"] += 301
    result = analyze(client, request)
    assert result.summary.total_reps == 1 and result.status == "partial"


def test_nonincreasing_timestamps_are_rejected():
    with pytest.raises(ValueError, match="strictly increase"):
        segment_incline_presses([AngleSample(100, 90), AngleSample(100, 160)])


def test_expired_press_does_not_complete_without_new_readiness():
    angles = READY + [120] * 160 + [160] * 10
    assert not segment_incline_presses([AngleSample(i * 100, a) for i, a in enumerate(angles)]).reps
