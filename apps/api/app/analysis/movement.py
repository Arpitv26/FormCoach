"""Stateless movement analysis from caller-supplied poses, independent of a pose SDK."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from app.analysis.exercises.base import ExerciseProfile
from app.analysis.exercises.cable_lateral_raise import segment_cable_lateral_raises
from app.analysis.exercises.gym_torso import add_torso_measurements
from app.analysis.exercises.incline_press import segment_incline_presses
from app.analysis.exercises.lat_pulldown import segment_lat_pulldowns
from app.analysis.exercises.pushup_body_line import add_body_line_measurements
from app.analysis.exercises.pushup_comparisons import compare_pushup_reps
from app.analysis.exercises.pushup_measurements import pushup_measurements
from app.analysis.exercises.pushup_observations import observe_body_line
from app.analysis.exercises.pushup_segmentation import segment_pushups
from app.analysis.exercises.squat_segmentation import segment_squats
from app.analysis.geometry import AngleMeasurement, measure_joint_angle
from app.analysis.placeholder import PlaceholderAnalyzer
from app.analysis.rep_segmentation import AngleSample, RepSegment, SegmentationResult
from app.analysis.tracking_feedback import tracking_feedback
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
    "incline-dumbbell-bench-press": MovementSpec(
        ("shoulder", "elbow", "wrist"),
        "top",
        "a visible bent-arm starting position",
        segment_incline_presses,
    ),
    "cable-lateral-raise": MovementSpec(
        ("hip", "shoulder", "elbow"),
        "top",
        "the lowered working arm beside your torso",
        segment_cable_lateral_raises,
    ),
    "lat-pulldown": MovementSpec(
        ("shoulder", "elbow", "wrist"),
        "extended",
        "the arms-overhead return position",
        segment_lat_pulldowns,
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
    measurements = {
        f"minSmoothed{side.title()}{joint.title()}AngleDeg": segment.min_angle_deg,
        "durationMs": segment.end_ms - segment.start_ms,
    }
    if joint in {"elbow", "shoulder"}:
        measurements.update(pushup_measurements(segment, side, joint=joint))
    return RepAnalysis(
        rep_number=number,
        start_ms=segment.start_ms,
        end_ms=segment.end_ms,
        score=None,
        metrics=RepMetrics(range_of_motion=None, symmetry=None, tempo=None, stability=None),
        measurements=measurements,
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
            response.limitations.append("Select an implemented exercise to use a rep counter.")
            return response

        movement = MOVEMENTS[profile.id]
        joint = movement.joints[1]
        side, measurements = _joint_measurements(
            frames, profile, image_width, image_height, movement.joints
        )
        samples = [
            AngleSample(frame.timestamp_ms, measurement.angle_deg)
            for frame, measurement in zip(frames, measurements, strict=True)
        ]
        result = movement.segment(samples)
        reps = [_rep_result(rep, index, side, joint) for index, rep in enumerate(result.reps, 1)]
        comparison_limitations = []
        observations = []
        if profile.id in {"lat-pulldown", "cable-lateral-raise"} and side:
            reps = add_torso_measurements(
                reps,
                frames,
                side=side,
                image_width=image_width,
                image_height=image_height,
                minimum_visibility=profile.minimum_visibility,
            )
        if profile.id == "push-up" and side:
            observations = observe_body_line(
                frames,
                side=side,
                image_width=image_width,
                image_height=image_height,
                minimum_visibility=profile.minimum_visibility,
                is_final=is_final,
            )
            reps = add_body_line_measurements(
                reps,
                frames,
                side=side,
                image_width=image_width,
                image_height=image_height,
                minimum_visibility=profile.minimum_visibility,
            )
            comparisons = compare_pushup_reps(reps, samples, side, profile)
            reps = comparisons.reps
            comparison_limitations = comparisons.limitations
        if profile.id in {"incline-dumbbell-bench-press", "cable-lateral-raise"}:
            for rep in reps:
                rep.key_moments.append(
                    KeyMoment(
                        timestamp_ms=rep.end_ms,
                        type="raised_position" if joint == "shoulder" else "press_completed",
                        label="Arm reached the raised zone"
                        if joint == "shoulder"
                        else "Press reached the extension zone",
                    )
                )
        issues = [issue for rep in reps for issue in rep.issues]
        unavailable = sum(measurement.angle_deg is None for measurement in measurements)
        camera_issues = ["Camera orientation and full-body visibility have not been evaluated."]
        camera_issues.extend(
            tracking_feedback(
                frames,
                side=side,
                joints=movement.joints,
                image_width=image_width,
                image_height=image_height,
                minimum_visibility=profile.minimum_visibility,
                include_body_line=profile.id == "push-up",
            )
        )
        limitations = [
            "Tracking coverage counts received samples, not elapsed time or current readiness. "
            "Passing landmark checks does not establish camera angle, full-body visibility "
            "or form quality.",
            f"2D {joint} angles use supplied landmarks; their camera origin cannot be verified.",
            "Use a side view. Camera orientation is not validated; angles are not calibrated 3D.",
            f"Uncalibrated {profile.id} rules count observed movement under its selected profile. "
            "Shallow, fast, or interrupted attempts may not count; this is not a form judgment.",
            "Scores, biomechanical form assessment, and automatic exercise recognition "
            "are not implemented. "
            "The exercise is a user selection. Empty issues do not establish good form.",
        ]
        if side:
            limitations.append(
                f"Uses the {side} {joint} throughout this set (first usable side; left wins ties). "
                "Three-sample median smoothing and phase confirmation delay event timestamps."
            )
        if profile.id == "push-up":
            limitations.append(
                "Movement observations review sustained 2D shoulder-hip-ankle bends below "
                "150 degrees for at least 500 ms, with no gaps over 300 ms and a mostly "
                "horizontal shoulder-to-ankle direction. This uncalibrated rule is independent "
                "of counted reps; it cannot distinguish hip sag from pike, measure spinal "
                "posture, identify attempts or confirm correct form. Empty observations do "
                "not establish a straight body line. Live intervals appear after they close."
            )
            limitations.append(
                "Push-up counter v2 uses a 150-degree return zone and 100-degree bend zone, "
                "with 60 ms of consecutive observations plus median confirmation. "
                "These count movement cycles, not full lockout, depth quality or correct form."
            )
            limitations.append(
                "Body-line angles are sample medians of raw 2D shoulder-hip-ankle angles "
                "over each counted rep, using the same side as the elbow. Require at least "
                "three usable samples, both rep boundaries, no unavailable angles and no "
                "gap over 300 ms; otherwise the median is null. This unsigned angle cannot "
                "distinguish hip sag from pike, measure spinal posture or establish good form. "
                "A median can hide brief deviations; camera orientation is not validated."
            )
            limitations.append(
                "Elbow excursion is the observed 2D maximum minus minimum from confirmed "
                "descent through completion, not a calibrated full range-of-motion score. "
                "Time to/from minimum splits the counted interval at its first lowest angle; "
                "it includes pauses and confirmation delay, not isolated lowering/lifting time."
            )
            limitations.append(
                "Comparison flags are uncalibrated review heuristics, not bad-form or fatigue "
                "detections. Each rep needs two preceding completed reps with continuous tracking; "
                "timing must differ substantially from both references in the same direction. "
                "Unstable range references are skipped. Camera/view stability is not evaluated. "
                "Absent comparison keys mean unavailable, not no change."
            )
            limitations.extend(comparison_limitations)
        if profile.id == "lat-pulldown":
            limitations.append(
                "Lat-pulldown counter v1 uses a 120-degree elbow return zone and "
                "70-degree pulled zone, with 100 ms of raw observations plus median "
                "confirmation. One rep runs from a pull through the overhead return. "
                "These are uncalibrated counting zones, not full-extension or depth targets. "
                "Elbow excursion and timing describe the observed cycle. Equipment, torso "
                "swing, bilateral symmetry and form quality are not assessed. "
                "Automatic rep comparison flags are not implemented for this exercise."
            )
        if profile.id == "incline-dumbbell-bench-press":
            limitations.append(
                "Incline-press counter v1 confirms bent elbows <=100 degrees before each "
                "press, starts timing on the confirmed bent run and completes at >=150 degrees, "
                "with 100 ms raw dwell plus median confirmation. These are uncalibrated "
                "counting zones, not form or lockout targets. Timing and elbow excursion "
                "cover the bent-to-extended interval, including pauses/confirmation delay; "
                "lowering rearms the counter but is not part of that interval. "
                "Dumbbells, bench angle, bilateral symmetry and form are not evaluated. "
                "Automatic rep comparison flags are not implemented for this exercise."
            )
        if profile.id == "cable-lateral-raise":
            limitations.append(
                "Cable-raise counter v1 measures the projected hip-shoulder-elbow angle. "
                "It requires a lowered zone <=30 degrees then a raised zone >=60 degrees, "
                "100 ms raw dwell plus median confirmation. Returning low rearms the counter. "
                "Intervals run from the confirmed low run to the raised zone, including pauses; "
                "lowering before the low zone is excluded. These uncalibrated zones count visible "
                "lifts, not correct lateral raises or anatomical shoulder abduction. "
                "A side view strongly changes projected angles. Back-view footage has not "
                "produced reliable counts. Body rotation, cable path and form are not assessed. "
                "Automatic rep comparison flags are not implemented for this exercise."
            )
        if not side:
            camera_issues.append(f"No usable {'-'.join(movement.joints)} triplet on either side.")
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
                and (
                    result.current_phase == movement.ready_phase
                    or (
                        profile.id in {"incline-dumbbell-bench-press", "cable-lateral-raise"}
                        and result.current_phase == "bottom"
                    )
                )
                and not unavailable
                and not result.tracking_breaks
            ):
                status = "complete"
            headline = (
                f"{len(reps)} completed {profile.id} reps observed. Scores are not available yet."
            )
        unfinished = (
            {"ascent"}
            if profile.id in {"incline-dumbbell-bench-press", "cable-lateral-raise"}
            else {"descent", "bottom", "ascent"}
        )
        if is_final and result.current_phase in unfinished:
            limitations.append("The set ended during an unfinished repetition; it was not counted.")

        if issues:
            headline = (
                f"{len(reps)} completed push-up reps; {len(issues)} measured changes flagged "
                "for review. Scores are not available yet."
            )
        timeline = _timeline(reps)
        timeline.extend(
            TimelineEvent(
                timestamp_ms=issue.start_ms,
                type="issue",
                rep_number=rep.rep_number,
                issue_id=issue.id,
                label=issue.title,
            )
            for rep in reps
            for issue in rep.issues
        )
        timeline.sort(key=lambda event: event.timestamp_ms)
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
                primary_focus="rep_consistency_review" if issues else None,
                headline=headline,
            ),
            metrics=SessionMetrics(
                range_of_motion=None, symmetry=None, tempo=None, stability=None, consistency=None
            ),
            reps=reps,
            issues=issues,
            timeline=timeline,
            limitations=limitations,
            scoring=None,
            movement_observations=observations,
        )
