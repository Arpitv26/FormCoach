"""Stateless movement analysis from caller-supplied poses, independent of a pose SDK."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.analysis.exercises.base import ExerciseProfile
from app.analysis.exercises.pushup_segmentation import segment_pushups
from app.analysis.exercises.squat_segmentation import segment_squats
from app.analysis.geometry import AngleMeasurement, measure_joint_angle
from app.analysis.placeholder import PlaceholderAnalyzer
from app.analysis.rep_segmentation import AngleSample, RepSegment, SegmentationResult
from app.domain.analysis import (
    AnalysisResponse,
    CameraQuality,
    Exercise,
    KeyMoment,
    Provenance,
    RepAnalysis,
    RepMetrics,
    SessionMetrics,
    Source,
    Summary,
    TimelineEvent,
)
from app.domain.pose import PoseFrame


@dataclass(frozen=True)
class MovementSpec:
    joints: tuple[str, str, str]
    ready_phase: str
    ready_cue: str
    segment: Callable[[Sequence[AngleSample]], SegmentationResult]


MOVEMENTS = {
    "squat": MovementSpec(("hip", "knee", "ankle"), "standing", "standing", segment_squats),
    "push-up": MovementSpec(
        ("shoulder", "elbow", "wrist"), "top", "the straight-arm top position", segment_pushups
    ),
}


def _joint_measurements(
    frames: Sequence[PoseFrame],
    profile: ExerciseProfile,
    width: int,
    height: int,
    joints: tuple[str, str, str],
) -> tuple[str | None, list[AngleMeasurement]]:
    """Lock to the first usable side; left wins a tie. Appending frames cannot switch it."""
    side = None
    measurements = []
    for frame in frames:
        measurement = AngleMeasurement(None, "unusable_landmarks")
        for candidate in (side,) if side else ("left", "right"):
            measurement = measure_joint_angle(
                frame,
                tuple(f"{candidate}_{joint}" for joint in joints),
                image_width=width,
                image_height=height,
                minimum_visibility=profile.minimum_visibility,
            )
            if measurement.angle_deg is not None:
                side = candidate
                break
        measurements.append(measurement)
    return side, measurements


def _rep_result(segment: RepSegment, number: int, side: str, joint: str) -> RepAnalysis:
    return RepAnalysis(
        rep_number=number,
        start_ms=segment.start_ms,
        end_ms=segment.end_ms,
        score=None,
        metrics=RepMetrics(range_of_motion=None, symmetry=None, tempo=None, stability=None),
        measurements={
            f"minSmoothed{side.title()}{joint.title()}AngleDeg": segment.min_angle_deg,
            "durationMs": segment.end_ms - segment.start_ms,
        },
        issues=[],
        key_moments=[
            KeyMoment(
                timestamp_ms=segment.bottom_ms,
                type=f"minimum_{joint}_angle",
                label=f"Lowest smoothed {side} {joint} angle (2D)",
            )
        ],
    )


def _timeline(reps: Sequence[RepAnalysis]) -> list[TimelineEvent]:
    return [
        TimelineEvent(
            timestamp_ms=timestamp,
            type=event_type,
            rep_number=rep.rep_number,
            issue_id=None,
            label=label,
        )
        for rep in reps
        for timestamp, event_type, label in (
            (rep.start_ms, "rep_start", f"Rep {rep.rep_number} start"),
            (
                rep.key_moments[0].timestamp_ms,
                "key_moment",
                rep.key_moments[0].label,
            ),
            (rep.end_ms, "rep_end", f"Rep {rep.rep_number} completed"),
        )
    ]


class RuleBasedAnalyzer:
    def analyze(
        self,
        frames: Sequence[PoseFrame],
        *,
        session_id: str,
        source: Source,
        image_width: int,
        image_height: int,
        profile: ExerciseProfile | None,
        is_final: bool,
    ) -> AnalysisResponse:
        if profile is None or profile.id not in MOVEMENTS:
            response = PlaceholderAnalyzer().analyze(
                frames,
                session_id=session_id,
                source=source,
                image_width=image_width,
                image_height=image_height,
                profile=profile,
                is_final=is_final,
            )
            response.limitations.append(
                "Select push-up or squat to use an implemented rep counter."
            )
            return response

        movement = MOVEMENTS[profile.id]
        joint = movement.joints[1]
        side, measurements = _joint_measurements(
            frames, profile, image_width, image_height, movement.joints
        )
        result = movement.segment(
            [
                AngleSample(frame.timestamp_ms, measurement.angle_deg)
                for frame, measurement in zip(frames, measurements, strict=True)
            ]
        )
        reps = [_rep_result(rep, index, side, joint) for index, rep in enumerate(result.reps, 1)]
        unavailable = sum(measurement.angle_deg is None for measurement in measurements)
        camera_issues = ["Camera orientation and full-body visibility have not been evaluated."]
        limitations = [
            f"2D {joint} angles use supplied landmarks; their camera origin cannot be verified.",
            "Use a side view. Camera orientation is not validated; angles are not calibrated 3D.",
            f"Uncalibrated {profile.id} rules count observed extension-flexion-extension cycles. "
            "Shallow, fast, or interrupted attempts may not count; this is not a form judgment.",
            "Scores, form issues, and automatic exercise recognition are not implemented. "
            "The exercise is a user selection. Empty issues do not establish good form.",
        ]
        if side:
            limitations.append(
                f"Uses the {side} {joint} throughout this set (first usable side; left wins ties). "
                "Three-sample median smoothing and phase confirmation delay event timestamps."
            )
        else:
            camera_issues.append(f"No usable {'-'.join(movement.joints)} triplet on either side.")
        if unavailable:
            camera_issues.append(
                f"{joint.title()} angle unavailable in {unavailable} of {len(frames)} frames: "
                "missing, outside-frame, low/unknown visibility, or coincident landmarks."
            )
        if unavailable or result.tracking_breaks:
            limitations.append(
                f"Incomplete tracking: {unavailable} unavailable frames and "
                f"{result.tracking_breaks} tracking breaks. Completed reps are retained; "
                f"the count may omit movement during gaps. Resume from {movement.ready_cue}."
            )

        has_evidence = bool(reps) or result.current_phase != "unknown"
        if not has_evidence:
            status = "insufficient_data"
            headline = (
                f"Waiting for visible {', '.join(movement.joints)} joints and {movement.ready_cue}."
            )
            limitations.append(
                f"Need continuous observations of {movement.ready_cue} to establish readiness."
            )
        else:
            status = "partial"
            if (
                is_final
                and result.current_phase == movement.ready_phase
                and not unavailable
                and not result.tracking_breaks
            ):
                status = "complete"
            headline = (
                f"{len(reps)} completed {profile.id} reps observed. Scores are not available yet."
            )
        if is_final and result.current_phase in {"descent", "bottom", "ascent"}:
            limitations.append("The set ended during an unfinished repetition; it was not counted.")

        return AnalysisResponse(
            contract_version="1.0",
            session_id=session_id,
            status=status,
            provenance=Provenance(kind="measured", label="Computed from supplied pose landmarks"),
            source=source,
            exercise=Exercise(id=profile.id, name=profile.name, confidence=None),
            camera_quality=CameraQuality(score=None, full_body_visible=None, issues=camera_issues),
            summary=Summary(
                overall_score=None,
                total_reps=len(reps) if has_evidence else None,
                primary_focus=None,
                headline=headline,
            ),
            metrics=SessionMetrics(
                range_of_motion=None, symmetry=None, tempo=None, stability=None, consistency=None
            ),
            reps=reps,
            issues=[],
            timeline=_timeline(reps),
            limitations=limitations,
            scoring=None,
        )
