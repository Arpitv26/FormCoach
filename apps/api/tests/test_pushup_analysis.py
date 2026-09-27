"""Synthetic push-up elbow motion: validates mechanics, not real-camera accuracy."""

import pytest
from test_live_analysis import CYCLE, STANDING, analyze, squat_request

from app.analysis.exercises.pushup_segmentation import segment_pushups
from app.analysis.rep_segmentation import AngleSample


def pushup_request(angles=None, *, side="left", final=False):
    request = squat_request(angles, side=side, final=final)
    request["exerciseHint"] = "push-up"
    request["sessionId"] = "synthetic-pushup-test"
    for frame in request["frames"]:
        for landmark, joint in zip(frame["landmarks"], ("shoulder", "elbow", "wrist"), strict=True):
            landmark["index"] -= 12
            landmark["name"] = f"{side}_{joint}"
    return request


def test_pushup_phases_and_three_completed_cycles():
    samples = [AngleSample(index * 100, angle) for index, angle in enumerate(STANDING + CYCLE * 3)]
    phases = [segment_pushups(samples[:end]).current_phase for end in (5, 10, 15, 20, 25)]
    assert phases == ["top", "descent", "bottom", "ascent", "top"]
    assert len(segment_pushups(samples).reps) == 3
    assert segment_pushups(samples) == segment_pushups(samples)


def test_top_dwell_starts_on_the_frame_that_confirms_ascent():
    # A short recording ends after enough observed extension. Confirming ascent
    # must not discard the first top observation and require an extra frame.
    angles = STANDING + [140] * 5 + [90] * 5 + [130] * 2 + [170] * 4
    samples = [AngleSample(index * 100, angle) for index, angle in enumerate(angles)]
    result = segment_pushups(samples)
    assert len(result.reps) == 1
    assert result.reps[0].end_ms == 2000
    assert result.current_phase == "top"
    assert not segment_pushups(samples[:-1]).reps  # Full dwell is still required.


def test_brief_top_spike_during_ascent_does_not_complete_a_rep():
    angles = STANDING + [140] * 5 + [90] * 5 + [130] * 2 + [170] * 2 + [130] * 4
    samples = [AngleSample(index * 100, angle) for index, angle in enumerate(angles)]
    assert not segment_pushups(samples).reps


@pytest.mark.parametrize("side", ["left", "right"])
def test_pushup_http_measures_elbow_not_knee_and_keeps_scores_unknown(client, side):
    result = analyze(client, pushup_request(side=side, final=True))
    assert result.status == "complete"
    assert result.exercise.id == "push-up" and result.exercise.confidence is None
    assert result.summary.total_reps == 1
    rep = result.reps[0]
    assert rep.measurements == {
        f"minSmoothed{side.title()}ElbowAngleDeg": pytest.approx(90),
        "durationMs": 1700,
        f"maxSmoothed{side.title()}ElbowAngleDeg": pytest.approx(170),
        f"smoothed{side.title()}ElbowExcursionDeg": pytest.approx(80),
        "angleMeasurementStartMs": 800,
        "timeToMinElbowAngleMs": 500,
        "timeFromMinElbowAngleMs": 1200,
        "bodyLineSampleCount": 18,
        "bodyLineUsableSampleCount": 0,
        f"median{side.title()}ShoulderHipAnkleAngleDeg": None,
    }
    assert (rep.start_ms, rep.end_ms) == (600, 2300)
    assert rep.key_moments[0].type == "minimum_elbow_angle"
    assert result.summary.overall_score is None and rep.score is None
    assert not result.issues and result.scoring is None
    assert all("knee" not in item and "standing" not in item for item in result.limitations)


@pytest.mark.parametrize(
    "angles", [[], [90] * 15, STANDING + CYCLE[:15], STANDING + [140] * 5 + [120] * 5 + STANDING]
)
def test_no_partial_or_shallow_pushups_are_invented(client, angles):
    result = analyze(client, pushup_request(angles, final=True))
    assert not result.reps
    assert result.summary.total_reps in (None, 0)


@pytest.mark.parametrize("failure", ["missing", "unknown", "low", "outside", "gap"])
def test_pushup_lost_tracking_discards_only_unfinished_cycle(client, failure):
    request = pushup_request(STANDING + CYCLE * 2, final=True)
    frame = request["frames"][33]
    if failure == "missing":
        frame["landmarks"] = []
    elif failure == "unknown":
        frame["landmarks"][1]["visibility"] = None
    elif failure == "low":
        frame["landmarks"][1]["visibility"] = 0.69
    elif failure == "outside":
        frame["landmarks"][1]["x"] = -0.01
    else:
        for later in request["frames"][33:]:
            later["timestampMs"] += 301
    result = analyze(client, request)
    assert result.status == "partial"
    assert result.summary.total_reps == 1
    assert any("straight-arm top" in item for item in result.limitations)


def test_pushup_side_is_locked_and_cannot_bridge_occlusion(client):
    request = pushup_request()
    right = pushup_request(side="right")
    for frame, other in zip(request["frames"], right["frames"], strict=True):
        frame["landmarks"].extend(other["landmarks"])
    request["frames"][13]["landmarks"] = right["frames"][13]["landmarks"]
    result = analyze(client, request)
    assert not result.reps
    assert any("Uses the left elbow" in item for item in result.limitations)


def test_knee_landmarks_alone_do_not_become_pushup_measurements(client):
    request = squat_request()
    request["exerciseHint"] = "push-up"
    result = analyze(client, request)
    assert result.status == "insufficient_data"
    assert result.summary.total_reps is None
    assert any("shoulder-elbow-wrist" in item for item in result.camera_quality.issues)


def test_pushup_cumulative_results_are_stable(client):
    request = pushup_request(STANDING + CYCLE * 3)
    previous = []
    for end in (10, 25, 45, 65):
        snapshot = {**request, "frames": request["frames"][:end]}
        result = analyze(client, snapshot)
        assert result.reps[: len(previous)] == previous
        assert result == analyze(client, snapshot)
        previous = result.reps
    assert result.summary.total_reps == 3
