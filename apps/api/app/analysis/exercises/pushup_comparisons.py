"""Causal within-set review flags. Thresholds are uncalibrated demo heuristics."""

from collections.abc import Sequence
from statistics import median

from app.analysis.angle_segmentation import AngleCycleConfig
from app.analysis.exercises.base import ExerciseProfile
from app.analysis.rep_segmentation import AngleSample
from app.domain.analysis import Issue, RepAnalysis

MAX_COMPARISON_GAP_MS = AngleCycleConfig().maximum_gap_ms


def _continuous(samples: Sequence[AngleSample], start_ms: int, end_ms: int) -> bool:
    window = [sample for sample in samples if start_ms <= sample.timestamp_ms <= end_ms]
    return (
        bool(window)
        and window[0].timestamp_ms == start_ms
        and window[-1].timestamp_ms == end_ms
        and all(sample.angle_deg is not None for sample in window)
        and all(
            0 < b.timestamp_ms - a.timestamp_ms <= MAX_COMPARISON_GAP_MS
            for a, b in zip(window, window[1:], strict=False)
        )
    )


def _issue(rep: RepAnalysis, side: str, code: str, title: str, explanation: str) -> Issue:
    return Issue(
        id=f"push-up-rep-{rep.rep_number}-{code.lower()}",
        code=code,
        severity="low",
        confidence=None,
        title=title,
        short_cue="Review this rep alongside the two preceding reps in the same camera view.",
        explanation=explanation + " This is a measured difference, not a judgment of form quality.",
        start_ms=rep.start_ms,
        end_ms=rep.end_ms,
        involved_joints=[f"{side}_{joint}" for joint in ("shoulder", "elbow", "wrist")],
    )


def compare_pushup_reps(
    reps: Sequence[RepAnalysis],
    samples: Sequence[AngleSample],
    side: str,
    profile: ExerciseProfile,
) -> list[RepAnalysis]:
    """Each completed rep uses only its two predecessors; never revise an earlier rep.

    Missing observations anywhere from the first reference's start through this rep's
    end suppress both comparisons. Reference stability is evaluated separately per metric.
    """
    compared = [rep.model_copy(deep=True) for rep in reps]
    thresholds = profile.thresholds
    excursion_key = f"smoothed{side.title()}ElbowExcursionDeg"
    for index in range(2, len(compared)):
        rep = compared[index]
        references = compared[index - 2 : index]
        if not _continuous(samples, references[0].start_ms, rep.end_ms):
            continue
        durations = [ref.measurements.get("durationMs") for ref in references]
        excursions = [ref.measurements.get(excursion_key) for ref in references]
        reference_label = f"reps {references[0].rep_number}–{references[1].rep_number}"
        values: dict[str, float] = {}
        if all(value is not None and value > 0 for value in durations):
            baseline = median(durations)
            current = rep.measurements.get("durationMs")
            stable = (max(durations) - min(durations)) / baseline <= thresholds[
                "maximumReferenceDurationSpreadFraction"
            ]
            if stable and current is not None and current > 0:
                delta = current - baseline
                trigger = max(
                    thresholds["minimumDurationChangeMs"],
                    baseline * thresholds["durationChangeFraction"],
                )
                values.update(
                    referenceMedianDurationMs=baseline,
                    durationDeltaMs=delta,
                    durationDeltaPercent=100 * delta / baseline,
                    durationChangeThresholdMs=trigger,
                )
                if abs(delta) >= trigger:
                    direction = "longer" if delta > 0 else "shorter"
                    rep.issues.append(
                        _issue(
                            rep,
                            side,
                            "PUSHUP_REP_DURATION_CHANGED",
                            "Counted rep time changed",
                            f"Rep {rep.rep_number} took {current / 1000:.2f} s versus "
                            f"{baseline / 1000:.2f} s for the median of {reference_label}: "
                            f"{abs(delta) / 1000:.2f} s {direction}. The review threshold is "
                            f"{trigger / 1000:.2f} s. Timing includes pauses "
                            "and confirmation delay.",
                        )
                    )
        if all(value is not None and value > 0 for value in excursions):
            baseline = median(excursions)
            current = rep.measurements.get(excursion_key)
            stable = (
                max(excursions) - min(excursions)
                <= thresholds["maximumReferenceExcursionSpreadDeg"]
            )
            if stable and current is not None and current >= 0:
                delta = current - baseline
                trigger = max(
                    thresholds["minimumExcursionReductionDeg"],
                    baseline * thresholds["excursionReductionFraction"],
                )
                values.update(
                    referenceMedianElbowExcursionDeg=baseline,
                    elbowExcursionDeltaDeg=delta,
                    elbowExcursionDeltaPercent=100 * delta / baseline,
                    elbowExcursionReductionThresholdDeg=trigger,
                )
                if -delta >= trigger:
                    rep.issues.append(
                        _issue(
                            rep,
                            side,
                            "PUSHUP_ELBOW_EXCURSION_REDUCED",
                            "Observed elbow range reduced",
                            f"Rep {rep.rep_number} had {current:.1f}° of observed {side} elbow "
                            f"excursion versus {baseline:.1f}° for the median of "
                            f"{reference_label}: "
                            f"{-delta:.1f}° less. The review threshold is {trigger:.1f}°. "
                            "This uses 2D angles; changes in camera view or pose estimates "
                            "can affect it.",
                        )
                    )
        if values:
            rep.measurements.update(
                comparisonReferenceStartRep=references[0].rep_number,
                comparisonReferenceEndRep=references[1].rep_number,
                **values,
            )
    return compared
