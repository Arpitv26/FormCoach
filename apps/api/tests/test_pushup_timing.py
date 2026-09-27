"""Timing policy v2 boundaries, variable references and unavailable explanations."""

import pytest
from test_pushup_comparisons import DURATION, compare, inputs

from app.analysis.exercises.pushup import PUSHUP_PROFILE
from app.analysis.exercises.pushup_comparisons import compare_pushup_reps
from app.analysis.rep_segmentation import AngleSample


@pytest.mark.parametrize(
    "current,flag",
    [(1189, True), (1190, True), (1191, False), (2989, False), (2990, True), (2991, True)],
)
def test_different_references_require_change_from_both_at_inclusive_boundaries(current, flag):
    reps, samples = inputs(durations=(1700, 2300, current), ranges=(80,) * 3)
    result = compare(reps, samples)[-1]
    assert bool(result.issues) == flag
    values = result.measurements
    assert values["durationReviewLowerBoundMs"] == 1190
    assert values["durationReviewUpperBoundMs"] == 2990
    assert values["referenceMedianDurationMs"] == 2000
    assert values["durationChangeThresholdMs"] == (810 if current < 2000 else 990)
    assert values["durationComparisonVersion"] == 2


@pytest.mark.parametrize("current,flag", [(1899, False), (1900, True)])
def test_absolute_floor_applies_to_each_reference(current, flag):
    reps, samples = inputs(durations=(1000, 1400, current), ranges=(80,) * 3)
    result = compare(reps, samples)[-1]
    assert bool(result.issues) == flag
    assert result.measurements["durationReviewUpperBoundMs"] == 1900


@pytest.mark.parametrize("current", [1400, 2000, 3000])
def test_between_reference_durations_never_flags(current):
    reps, samples = inputs(durations=(1400, 3000, current), ranges=(80,) * 3)
    result = compare(reps, samples)[-1]
    assert not result.issues
    assert "referenceMedianDurationMs" in result.measurements


@pytest.mark.parametrize("side", ["left", "right"])
def test_slow_third_then_return_toward_earlier_pace_does_not_flag_fourth(side):
    # Authored durations deliberately differ from the private recording.
    reps, samples = inputs(durations=(1800, 1400, 3300, 1200), ranges=(80,) * 4, side=side)
    result = compare(reps, samples, side)
    assert [i.code for i in result[2].issues] == [DURATION]
    assert not result[3].issues
    assert result[3].measurements["durationReviewLowerBoundMs"] == 900


@pytest.mark.parametrize("value", [None, 0, -1, 9999])
@pytest.mark.parametrize("index", [0, 2])
def test_invalid_or_timestamp_inconsistent_duration_has_explanation(index, value):
    reps, samples = inputs(ranges=(80,) * 3)
    reps[index].measurements["durationMs"] = value
    result = compare_pushup_reps(reps, samples, "left", PUSHUP_PROFILE)
    assert "referenceMedianDurationMs" not in result.reps[2].measurements
    assert any("Rep 3: timing comparison unavailable" in s for s in result.limitations)


def test_tracking_gap_explained_and_never_bridged_for_large_changes():
    reps, samples = inputs(durations=(1000, 1400, 4000), ranges=(80,) * 3)
    samples.insert(11, AngleSample(1050, None))
    result = compare_pushup_reps(reps, samples, "left", PUSHUP_PROFILE)
    assert result.reps == reps
    assert any("Rep 3: timing/range comparisons unavailable" in s for s in result.limitations)
    assert any("Reps 1–2" in s for s in result.limitations)


def test_missing_and_unstable_range_references_have_explanation_without_blocking_timing():
    reps, samples = inputs(durations=(1700, 2100, 3500), ranges=(80, 110, 100))
    result = compare_pushup_reps(reps, samples, "left", PUSHUP_PROFILE)
    assert [i.code for i in result.reps[2].issues] == [DURATION]
    assert any("Rep 3: range comparison unavailable" in s for s in result.limitations)


def test_empty_reps_have_no_spurious_comparison_limitations():
    result = compare_pushup_reps([], [], "left", PUSHUP_PROFILE)
    assert not result.reps and not result.limitations
