"""Known synthetic signals check units, timing, smoothing, and measurement isolation."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from test_live_analysis import CYCLE, STANDING, analyze
from test_pushup_analysis import pushup_request

from app.analysis.exercises.pushup_segmentation import segment_pushups
from app.analysis.rep_segmentation import AngleSample
from app.domain.analysis import AnalysisResponse


def segment(angles):
    return segment_pushups([AngleSample(i * 100, angle) for i, angle in enumerate(angles)])


def test_extrema_use_causal_median_and_ignore_single_frame_spike():
    angles = STANDING + CYCLE
    angles[12] = 10
    rep = segment(angles).reps[0]
    assert rep.min_angle_deg == 90
    assert rep.max_angle_deg == 170
    assert rep.angle_measurement_start_ms == 600
    assert (rep.start_ms, rep.bottom_ms, rep.end_ms) == (500, 1100, 2100)


def test_each_rep_has_its_own_range_and_later_top_pause_cannot_change_it(client):
    first = [140] * 5 + [80] * 5 + [130] * 5 + [175] * 5
    second = [140] * 5 + [95] * 5 + [130] * 5 + [165] * 5
    result = analyze(client, pushup_request(STANDING + first + second, final=True))
    assert result.summary.total_reps == 2
    measurements = [rep.measurements for rep in result.reps]
    assert measurements[0]["smoothedLeftElbowExcursionDeg"] == pytest.approx(95)
    assert measurements[1]["smoothedLeftElbowExcursionDeg"] == pytest.approx(70)
    longer = analyze(client, pushup_request(STANDING + first + second + [179] * 10, final=True))
    assert longer.reps == result.reps


def test_timing_uses_source_milliseconds_not_frame_count(client):
    request = pushup_request(final=True)
    timestamps = [0]
    for i in range(1, len(request["frames"])):
        timestamps.append(timestamps[-1] + (90 if i % 2 else 110))
    for frame, timestamp in zip(request["frames"], timestamps, strict=True):
        frame["timestampMs"] = timestamp
    rep = analyze(client, request).reps[0]
    m = rep.measurements
    assert m["durationMs"] == timestamps[21] - timestamps[5]
    assert m["timeToMinElbowAngleMs"] == timestamps[11] - timestamps[5]
    assert m["timeFromMinElbowAngleMs"] == timestamps[21] - timestamps[11]
    assert m["timeToMinElbowAngleMs"] + m["timeFromMinElbowAngleMs"] == m["durationMs"]
    assert m["angleMeasurementStartMs"] == timestamps[6]


def test_bottom_plateau_uses_first_minimum_and_does_not_claim_phase_durations(client):
    request = pushup_request(STANDING + [140] * 5 + [90] * 10 + [130] * 5 + STANDING, final=True)
    result = analyze(client, request)
    m = result.reps[0].measurements
    assert m["timeToMinElbowAngleMs"] == 600
    assert m["timeFromMinElbowAngleMs"] == 1500  # Includes the bottom pause.
    assert result.reps[0].key_moments[0].timestamp_ms == 1100
    assert any("includes pauses" in message for message in result.limitations)
    assert all(value is None for value in result.reps[0].metrics.model_dump().values())


@pytest.mark.parametrize("lost", [None, 400])
def test_tracking_break_discards_partial_measurements_and_recovers(lost):
    angles = STANDING + CYCLE[:10] + [170] * 5 + CYCLE
    samples = [AngleSample(i * 100, angle) for i, angle in enumerate(angles)]
    if lost is None:
        samples[14] = AngleSample(1400, None)
    else:
        samples = [
            AngleSample(s.timestamp_ms + (lost if i >= 14 else 0), s.angle_deg)
            for i, s in enumerate(samples)
        ]
    reps = segment_pushups(samples).reps
    assert len(reps) == 1
    assert reps[0].angle_measurement_start_ms >= samples[20].timestamp_ms
    assert reps[0].max_angle_deg == 170 and reps[0].min_angle_deg == 90


def test_pushup_response_keeps_existing_schema_and_unknown_scores(client):
    response = analyze(client, pushup_request(final=True))
    root = Path(__file__).resolve().parents[3]
    schema = json.loads((root / "contracts/analysis.schema.json").read_text())
    Draft202012Validator(schema).validate(response.model_dump(by_alias=True))
    assert response.summary.overall_score is None and response.scoring is None
    assert not response.issues and all(
        value is None for value in response.metrics.model_dump().values()
    )


def test_synthetic_pushup_fixture_is_valid_and_clearly_labeled():
    root = Path(__file__).resolve().parents[3]
    response = AnalysisResponse.model_validate_json(
        (root / "contracts/examples/pushup-analysis.json").read_text()
    )
    assert response.provenance.kind == "synthetic"
    assert "SYNTHETIC" in response.provenance.label
    assert response.reps[0].measurements["smoothedLeftElbowExcursionDeg"] == pytest.approx(80)
