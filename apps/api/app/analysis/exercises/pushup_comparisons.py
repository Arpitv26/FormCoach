"""Causal within-set review flags. Thresholds are uncalibrated demo heuristics."""

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import median

from app.analysis.angle_segmentation import AngleCycleConfig
from app.analysis.exercises.base import ExerciseProfile
from app.analysis.exercises.pushup_timing import timing_measurements
from app.analysis.rep_segmentation import AngleSample
from app.domain.analysis import Issue, RepAnalysis

MAX_COMPARISON_GAP_MS = AngleCycleConfig().maximum_gap_ms


@dataclass(frozen=True)
class ComparisonResult:
    reps: list[RepAnalysis]
    limitations: list[str]


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
) -> ComparisonResult:
    """Each completed rep uses only its two predecessors; never revise an earlier rep.

    Missing observations anywhere from the first reference's start through this rep's
    end suppress both comparisons. Timing requires agreement against both prior durations;
    excursion retains its independent reference-stability gate.
    """
    compared = [rep.model_copy(deep=True) for rep in reps]
    limitations = []
    if compared:
        label = "Rep 1" if len(compared) == 1 else "Reps 1–2"
        limitations.append(f"{label}: comparisons unavailable with fewer than two preceding reps.")
    thresholds = profile.thresholds
    excursion_key = f"smoothed{side.title()}ElbowExcursionDeg"
    for index in range(2, len(compared)):
        rep = compared[index]
        references = compared[index - 2 : index]
        if not _continuous(samples, references[0].start_ms, rep.end_ms):
            limitations.append(
                f"Rep {rep.rep_number}: timing/range comparisons unavailable because tracking "
                "is incomplete across the reference/current reps, including between reps."
            )
            continue
        excursions = [ref.measurements.get(excursion_key) for ref in references]
        reference_label = f"reps {references[0].rep_number}–{references[1].rep_number}"
        values = timing_measurements(
            references,
            rep,
            floor_ms=thresholds["minimumDurationChangeMs"],
            fraction=thresholds["durationChangeFraction"],
        )
        if values:
            current = rep.measurements["durationMs"]
            lower = values["durationReviewLowerBoundMs"]
            upper = values["durationReviewUpperBoundMs"]
            if current <= lower or current >= upper:
                direction = "longer" if current >= upper else "shorter"
                boundary = upper if current >= upper else lower
                rep.issues.append(
                    _issue(
                        rep,
                        side,
                        "PUSHUP_REP_DURATION_CHANGED",
                        "Counted rep time changed",
                        f"Rep {rep.rep_number} took {current / 1000:.2f} s, "
                        f"substantially {direction} than both {reference_label} "
                        f"({references[0].measurements['durationMs'] / 1000:.2f} s and "
                        f"{references[1].measurements['durationMs'] / 1000:.2f} s). "
                        f"The {direction}-duration review boundary is {boundary / 1000:.2f} s. "
                        f"The threshold against each reference is the greater of "
                        f"{thresholds['minimumDurationChangeMs'] / 1000:.2f} s and "
                        f"{thresholds['durationChangeFraction'] * 100:g}%. "
                        "Timing includes pauses and confirmation delay.",
                    )
                )
        else:
            limitations.append(
                f"Rep {rep.rep_number}: timing comparison unavailable because a reference/current "
                "duration is missing, nonpositive or inconsistent with its rep timestamps."
            )
        excursion_available = False
        if all(value is not None and value > 0 for value in excursions):
            baseline = median(excursions)
            current = rep.measurements.get(excursion_key)
            stable = (
                max(excursions) - min(excursions)
                <= thresholds["maximumReferenceExcursionSpreadDeg"]
            )
            if stable and current is not None and current >= 0:
                excursion_available = True
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
        if not excursion_available:
            limitations.append(
                f"Rep {rep.rep_number}: range comparison unavailable because reference/current "
                "excursion is missing/invalid or the two reference excursions differ by more "
                f"than {thresholds['maximumReferenceExcursionSpreadDeg']:g}°."
            )
        if values:
            rep.measurements.update(
                comparisonReferenceStartRep=references[0].rep_number,
                comparisonReferenceEndRep=references[1].rep_number,
                **values,
            )
    return ComparisonResult(compared, limitations)
