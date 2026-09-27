"""Reviewed wording from numeric evidence; arbitrary analysis prose is never advice."""

from dataclasses import dataclass
from math import isclose
from statistics import median

from app.domain.models import AnalysisResponse, CoachRequest, CoachResponse


@dataclass(frozen=True)
class EvidenceCard:
    id: str
    text: str
    paths: tuple[str, ...]


def body_line_card(analysis: AnalysisResponse, index: int, side: str) -> EvidenceCard | None:
    """Describe supplied geometry only when its side and sample metadata are consistent.

    Called after the matching elbow range has been validated. The coach has no raw frames
    to recheck visibility, gaps or the median itself; this is not measurement authentication.
    """
    rep = analysis.reps[index]
    key = f"median{side}ShoulderHipAnkleAngleDeg"
    other_side = "Right" if side == "Left" else "Left"
    angle = rep.measurements.get(key)
    total = rep.measurements.get("bodyLineSampleCount")
    usable = rep.measurements.get("bodyLineUsableSampleCount")
    if (
        angle is None
        or not 0 <= angle <= 180
        or total is None
        or not 3 <= total <= 1800
        or total != int(total)
        or usable != total
        or rep.measurements.get(f"median{other_side}ShoulderHipAnkleAngleDeg") is not None
    ):
        return None
    path = f"reps.{index}"
    return EvidenceCard(
        f"rep-{rep.rep_number}-{side.lower()}-body-line",
        f"Rep {rep.rep_number} reports a median {side.lower()} shoulder–hip–ankle angle "
        f"of {angle:.1f}° across {int(total)} usable samples. "
        "This unsigned 2D angle cannot distinguish hip sag from pike or judge form. "
        "The median can hide brief changes; camera view and pose estimates affect it.",
        (
            f"{path}.repNumber",
            f"{path}.measurements.{key}",
            f"{path}.measurements.bodyLineSampleCount",
            f"{path}.measurements.bodyLineUsableSampleCount",
        ),
    )


def comparison(
    analysis: AnalysisResponse, index: int, key: str, current: float
) -> tuple[str, tuple[str, ...]]:
    """Corroborate supplied comparison values against the two actual preceding reps.

    This does not re-run pose visibility checks: only the analyzer has the pose frames.
    It describes numeric differences, never a threshold crossing or quality judgment.
    """
    if index < 2:
        return "", ()
    values = analysis.reps[index].measurements
    if (
        values.get("comparisonReferenceStartRep") != index - 1
        or values.get("comparisonReferenceEndRep") != index
    ):
        return "", ()
    references = [rep.measurements.get(key) for rep in analysis.reps[index - 2 : index]]
    if any(value is None or value <= 0 for value in references):
        return "", ()
    baseline = median(references)
    is_time = key == "durationMs"
    baseline_key = "referenceMedianDurationMs" if is_time else "referenceMedianElbowExcursionDeg"
    delta_key = "durationDeltaMs" if is_time else "elbowExcursionDeltaDeg"
    if values.get(baseline_key) is None or values.get(delta_key) is None:
        return "", ()
    if not isclose(values[baseline_key], baseline, abs_tol=0.01) or not isclose(
        values[delta_key], current - baseline, abs_tol=0.01
    ):
        return "", ()
    if is_time:
        if any(
            not isclose(rep.measurements[key], rep.end_ms - rep.start_ms, abs_tol=0.01)
            for rep in analysis.reps[index - 2 : index]
        ):
            return "", ()
        detail = (
            f" The median duration of reps {index - 1}–{index} is {baseline / 1000:.2f} s;"
            f" the difference is {(current - baseline) / 1000:+.2f} s."
        )
    else:
        if any(value > 180 for value in references):
            return "", ()
        detail = (
            f" The median excursion of reps {index - 1}–{index} is {baseline:.1f}°;"
            f" the difference is {current - baseline:+.1f}°."
            " Camera view and pose estimates can affect this difference."
        )
    paths = tuple(f"reps.{ref}.measurements.{key}" for ref in (index - 2, index - 1))
    paths += tuple(
        f"reps.{index}.measurements.{name}"
        for name in (
            "comparisonReferenceStartRep",
            "comparisonReferenceEndRep",
            baseline_key,
            delta_key,
        )
    )
    return detail, paths


def evidence_cards(
    analysis: AnalysisResponse, *, preferred_reps: tuple[int, ...] = ()
) -> list[EvidenceCard]:
    if analysis.status == "not_implemented" or analysis.provenance.kind == "placeholder":
        return []
    cards = []
    for index, observation in enumerate(analysis.movement_observations[:6]):
        path = f"movementObservations.{index}"
        cards.append(
            EvidenceCard(
                f"movement-{index + 1}-body-line",
                f"From {observation.start_ms / 1000:.2f} to "
                f"{observation.end_ms / 1000:.2f} s, the tracked {observation.side} "
                "shoulder, hip and ankle formed a sustained bend in the image. "
                f"The median angle was {observation.median_angle_deg:.1f}°, across "
                f"{observation.sample_count} samples, all below the provisional "
                "150° review threshold (180° would be a straight line). "
                "This can be reviewed even with zero counted reps. It does not identify "
                "hip sag versus pike, spinal posture, an attempt count or the reason reps "
                "did not count. Setup and other movements can trigger it; review the video.",
                tuple(
                    f"{path}.{key}"
                    for key in (
                        "startMs",
                        "endMs",
                        "side",
                        "medianAngleDeg",
                        "sampleCount",
                        "thresholdAngleDeg",
                    )
                ),
            )
        )
    if analysis.status == "insufficient_data":
        return cards
    score = analysis.summary.overall_score
    if score is not None:
        cards.append(
            EvidenceCard(
                "score",
                f"The supplied analysis reports an overall score of {score:g}/100.",
                ("summary.overallScore",),
            )
        )
    count = analysis.summary.total_reps
    if count is not None:
        cards.append(
            EvidenceCard(
                "count",
                f"The supplied analysis counts {count} completed rep(s).",
                ("summary.totalReps",),
            )
        )
    if analysis.exercise is None or analysis.exercise.id != "push-up":
        return cards
    # Bound the model input, but don't omit the very rep the user asked about.
    ordered = [
        i
        for number in preferred_reps
        for i, rep in enumerate(analysis.reps)
        if rep.rep_number == number
    ]
    ordered += [i for i, rep in enumerate(analysis.reps) if rep.issues]
    ordered += [0, len(analysis.reps) - 1]
    ordered += list(range(len(analysis.reps)))
    for index in list(dict.fromkeys(ordered))[:6]:
        if not 0 <= index < len(analysis.reps):
            continue
        rep = analysis.reps[index]
        path = f"reps.{index}"
        duration = rep.end_ms - rep.start_ms
        detail, paths = comparison(analysis, index, "durationMs", duration)
        cards.append(
            EvidenceCard(
                f"rep-{rep.rep_number}-time",
                f"Rep {rep.rep_number} spans {duration / 1000:.2f} s,"
                f" from {rep.start_ms / 1000:.2f} to {rep.end_ms / 1000:.2f} s"
                " on the session timeline. Timing includes pauses and confirmation delay." + detail,
                (f"{path}.repNumber", f"{path}.startMs", f"{path}.endMs", *paths),
            )
        )
        for side in ("Left", "Right"):
            keys = [
                f"minSmoothed{side}ElbowAngleDeg",
                f"maxSmoothed{side}ElbowAngleDeg",
                f"smoothed{side}ElbowExcursionDeg",
            ]
            minimum, maximum, excursion = [rep.measurements.get(key) for key in keys]
            if (
                minimum is None
                or maximum is None
                or excursion is None
                or not 0 <= minimum <= maximum <= 180
                or not isclose(maximum - minimum, excursion, abs_tol=0.01)
            ):
                continue
            detail, paths = comparison(analysis, index, keys[2], excursion)
            cards.append(
                EvidenceCard(
                    f"rep-{rep.rep_number}-{side.lower()}-range",
                    f"Rep {rep.rep_number} has {excursion:.1f}° of observed {side.lower()}"
                    f" elbow excursion ({minimum:.1f}° to {maximum:.1f}°)."
                    " This is a 2D measurement, not a form score." + detail,
                    (f"{path}.repNumber", *(f"{path}.measurements.{key}" for key in keys), *paths),
                )
            )
            body_line = body_line_card(analysis, index, side)
            if body_line is not None:
                cards.append(body_line)
    return cards


def render_coach(
    request: CoachRequest,
    cards: list[EvidenceCard],
    *,
    provider: str,
    note: str,
    unsupported: bool = False,
) -> CoachResponse:
    analysis = request.analysis
    prefix = "Demo data only. " if analysis.provenance.kind == "synthetic" else ""
    if analysis.provenance.kind == "placeholder":
        prefix = "Placeholder data only. "
    if analysis.status in {"insufficient_data", "not_implemented"}:
        message = "There is not enough measured analysis to give a form cue yet."
        cards = []
    elif unsupported:
        message = (
            "That question is not supported by the available coaching evidence."
            " This coach cannot assess medical conditions or injury risk."
        )
        cards = []
    else:
        message = " ".join(card.text for card in cards)
        if analysis.summary.overall_score is None:
            message += " The supplied analysis does not contain an overall score yet."
        if request.mode == "next_set":
            message += (
                " Keep the same side camera view for your next recording"
                " so the measurements can be compared."
            )
    limitations = [
        note,
        "Coaching describes supplied analysis; it cannot verify that client-submitted"
        " measurements came from a camera.",
    ]
    if analysis.status == "partial":
        limitations.append(
            "Analysis is partial; the count covers completed detected reps only"
            " and may miss other movement."
        )
    if (
        analysis.camera_quality.full_body_visible is not True
        or analysis.camera_quality.score is None
        or analysis.camera_quality.issues
    ):
        limitations.append(
            "Camera reliability is limited or unknown; angle, visibility,"
            " and occlusion can prevent reliable evaluation."
        )
    if analysis.issues:
        limitations.append(
            "Review flags are not judgments of form quality; low or unknown confidence"
            " cannot establish a biomechanical problem."
        )
    limitations += analysis.limitations + analysis.camera_quality.issues
    return CoachResponse(
        contract_version="1.0",
        session_id=analysis.session_id,
        mode=request.mode,
        provider=provider,
        message=prefix + message.strip(),
        evidence=list(dict.fromkeys(path for card in cards for path in card.paths)),
        limitations=list(dict.fromkeys(limitations)),
    )
