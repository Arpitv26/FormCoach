"""Explicit arithmetic and synthetic pose sequences; not a clinical rule validation."""

from copy import deepcopy

import pytest
from test_live_analysis import STANDING, analyze
from test_pushup_analysis import pushup_request

from app.analysis.exercises.pushup import PUSHUP_PROFILE
from app.analysis.exercises.pushup_comparisons import compare_pushup_reps
from app.analysis.rep_segmentation import AngleSample
from app.domain.analysis import KeyMoment, RepAnalysis, RepMetrics

DURATION = "PUSHUP_REP_DURATION_CHANGED"
RANGE = "PUSHUP_ELBOW_EXCURSION_REDUCED"


def inputs(durations=(2000, 2000, 2600), ranges=(80, 80, 64), side="left"):
    reps = []
    samples = []
    start = 0
    for number, (duration, excursion) in enumerate(zip(durations, ranges, strict=True), 1):
        end = start + duration
        reps.append(
            RepAnalysis(
                rep_number=number,
                start_ms=start,
                end_ms=end,
                score=None,
                metrics=RepMetrics(range_of_motion=None, symmetry=None, tempo=None, stability=None),
                measurements={
                    "durationMs": duration,
                    f"smoothed{side.title()}ElbowExcursionDeg": excursion,
                },
                issues=[],
                key_moments=[
                    KeyMoment(
                        timestamp_ms=start + 500,
                        type="minimum_elbow_angle",
                        label="Synthetic minimum",
                    )
                ],
            )
        )
        times = sorted(set([*range(start, end, 100), end]))
        samples.extend(AngleSample(t, 120) for t in times)
        start = end + 100
    return reps, samples


def compare(reps, samples, side="left"):
    return compare_pushup_reps(reps, samples, side, PUSHUP_PROFILE).reps


@pytest.mark.parametrize("side", ["left", "right"])
def test_exact_threshold_flags_have_traceable_evidence_and_do_not_mutate_input(side):
    reps, samples = inputs(side=side)
    original = deepcopy(reps)
    result = compare(reps, samples, side)
    assert reps == original
    assert result[:2] == reps[:2]
    last = result[-1]
    assert [issue.code for issue in last.issues] == [DURATION, RANGE]
    assert last.measurements["durationDeltaMs"] == 600
    assert last.measurements["durationDeltaPercent"] == 30
    assert last.measurements["elbowExcursionDeltaDeg"] == -16
    assert last.measurements["elbowExcursionDeltaPercent"] == -20
    assert last.measurements["comparisonReferenceStartRep"] == 1
    assert last.measurements["comparisonReferenceEndRep"] == 2
    for issue in last.issues:
        assert issue.confidence is None and issue.severity == "low"
        assert "reps 1–2" in issue.explanation and "threshold" in issue.explanation
        assert issue.start_ms == last.start_ms and issue.end_ms == last.end_ms
        assert issue.involved_joints == [f"{side}_{j}" for j in ("shoulder", "elbow", "wrist")]


@pytest.mark.parametrize("current,flag", [(2599, False), (2600, True), (1400, True), (1401, False)])
def test_duration_percentage_boundary(current, flag):
    reps, samples = inputs(durations=(2000, 2000, current), ranges=(80, 80, 80))
    assert bool(compare(reps, samples)[-1].issues) == flag


@pytest.mark.parametrize("current,flag", [(1499, False), (1500, True)])
def test_duration_absolute_floor(current, flag):
    reps, samples = inputs(durations=(1000, 1000, current), ranges=(80, 80, 80))
    assert bool(compare(reps, samples)[-1].issues) == flag


@pytest.mark.parametrize("current,flag", [(64.1, False), (64, True), (100, False)])
def test_excursion_percentage_boundary_and_increase_is_not_reduction(current, flag):
    reps, samples = inputs(durations=(2000,) * 3, ranges=(80, 80, current))
    assert bool(compare(reps, samples)[-1].issues) == flag


@pytest.mark.parametrize("current,flag", [(35.1, False), (35, True)])
def test_excursion_absolute_floor(current, flag):
    reps, samples = inputs(durations=(2000,) * 3, ranges=(50, 50, current))
    assert bool(compare(reps, samples)[-1].issues) == flag


def test_reference_stability_is_independent_for_each_metric():
    reps, samples = inputs(durations=(1000, 2000, 3000))
    result = compare(reps, samples)[-1]
    assert [i.code for i in result.issues] == [DURATION, RANGE]
    assert result.measurements["referenceMedianDurationMs"] == 1500
    reps, samples = inputs(ranges=(80, 100, 50))
    result = compare(reps, samples)[-1]
    assert [i.code for i in result.issues] == [DURATION]
    assert "referenceMedianElbowExcursionDeg" not in result.measurements


@pytest.mark.parametrize("missing", [None, 0])
def test_missing_or_zero_reference_does_not_invent_a_comparison(missing):
    reps, samples = inputs()
    reps[0].measurements = {"durationMs": missing, "smoothedLeftElbowExcursionDeg": missing}
    assert compare(reps, samples)[-1] == reps[-1]


@pytest.mark.parametrize("break_type", ["missing", "gap"])
def test_no_comparison_across_tracking_breaks_even_between_reps(break_type):
    reps, samples = inputs()
    if break_type == "missing":
        samples[21] = AngleSample(samples[21].timestamp_ms, None)
    else:
        samples = [s for s in samples if not 1800 < s.timestamp_ms < 2300]
    assert compare(reps, samples) == reps


def test_two_new_references_allow_recovery_and_later_loss_preserves_earlier_flags():
    reps, samples = inputs(durations=(2000, 2000, 2600, 2000, 2000, 2600), ranges=(80,) * 6)
    # Rep 3 ends at 6800, rep 4 starts at 6900: loss is between those reps.
    samples = sorted([*samples, AngleSample(6850, None)], key=lambda s: s.timestamp_ms)
    results = compare(reps, samples)
    assert results[2].issues  # Completed before the loss.
    assert not results[3].issues and not results[4].issues
    assert results[5].issues  # References 4/5 and current 6 now have continuous coverage.
    assert results[5].measurements["comparisonReferenceStartRep"] == 4


def flagged_request():
    reference = [140] * 5 + [70] * 5 + [130] * 5 + [175] * 5
    changed = [140] * 10 + [98] * 10 + [130] * 10 + [162] * 5
    return pushup_request(STANDING + reference * 2 + changed, final=True)


def test_http_flags_link_rep_session_timeline_and_remain_stable(client):
    request = flagged_request()
    result = analyze(client, request)
    assert result.summary.total_reps == 3
    assert {issue.code for issue in result.issues} == {DURATION, RANGE}
    assert result.reps[2].issues == result.issues
    assert not result.reps[0].issues and not result.reps[1].issues
    events = [event for event in result.timeline if event.type == "issue"]
    assert {event.issue_id for event in events} == {issue.id for issue in result.issues}
    assert all(event.rep_number == 3 for event in events)
    assert result.timeline == sorted(result.timeline, key=lambda event: event.timestamp_ms)
    assert result.summary.primary_focus == "rep_consistency_review"
    assert result.scoring is None and result.summary.overall_score is None
    previous = []
    for stop in range(5, len(request["frames"]) + 1, 5):
        partial = analyze(client, {**request, "frames": request["frames"][:stop], "isFinal": False})
        assert partial.reps[: len(previous)] == previous
        previous = partial.reps
    assert result.reps == previous
    assert result == analyze(client, request)


def test_comparison_fixture_matches_existing_schema_and_is_explicitly_synthetic():
    import json
    from pathlib import Path

    from jsonschema import Draft202012Validator

    from app.domain.analysis import AnalysisResponse

    root = Path(__file__).resolve().parents[3]
    fixture = json.loads((root / "contracts/examples/pushup-comparison-analysis.json").read_text())
    Draft202012Validator(
        json.loads((root / "contracts/analysis.schema.json").read_text())
    ).validate(fixture)
    result = AnalysisResponse.model_validate(fixture)
    assert result.provenance.kind == "synthetic"
    assert "SYNTHETIC" in result.provenance.label
    assert result.summary.total_reps == 3
    assert {issue.code for issue in result.issues} == {DURATION, RANGE}
    assert result.reps[-1].measurements["durationDeltaMs"] == 1500
    assert result.reps[-1].measurements["elbowExcursionDeltaDeg"] == -41
    assert result.summary.overall_score is None
