"""Descriptive timing policy v2: require a substantial change from BOTH prior reps."""

from collections.abc import Sequence
from statistics import median

from app.domain.analysis import RepAnalysis


def timing_measurements(
    references: Sequence[RepAnalysis], current: RepAnalysis, *, floor_ms: float, fraction: float
) -> dict[str, float]:
    """Keep median deltas, but put review boundaries outside both reference durations.

    The same margin applies independently to each reference. This avoids interpreting a
    return to a previous pace as a new change just because the other reference was slow.
    These margins are demo heuristics, not calibrated movement-quality thresholds.
    """
    durations = [rep.measurements.get("durationMs") for rep in [*references, current]]
    if len(references) != 2 or any(
        value is None or value <= 0 or value != rep.end_ms - rep.start_ms
        for rep, value in zip([*references, current], durations, strict=True)
    ):
        return {}
    previous = durations[:2]
    baseline = median(previous)
    lower = min(value - max(floor_ms, fraction * value) for value in previous)
    upper = max(value + max(floor_ms, fraction * value) for value in previous)
    delta = durations[-1] - baseline
    return {
        "durationComparisonVersion": 2,
        "referenceMinDurationMs": min(previous),
        "referenceMaxDurationMs": max(previous),
        "referenceMedianDurationMs": baseline,
        "durationDeltaMs": delta,
        "durationDeltaPercent": 100 * delta / baseline,
        "durationReviewLowerBoundMs": lower,
        "durationReviewUpperBoundMs": upper,
        # Distance from median in the current direction, preserving the old field's units.
        "durationChangeThresholdMs": upper - baseline if delta >= 0 else baseline - lower,
    }
