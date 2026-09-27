"""Descriptive 2D observations; no target tempo, quality score, or form judgment."""

from app.analysis.rep_segmentation import RepSegment


def pushup_measurements(
    segment: RepSegment, side: str, *, joint: str = "elbow"
) -> dict[str, float | int]:
    """Use the counter's causal signal/window, never resmooth individual cropped reps.

    Extrema use the segment’s measurement-start boundary through completion.
    The minimum moment is the first occurrence of the exact lowest smoothed angle.
    Timing partitions the counted interval at that moment; it includes dwell/pauses.
    """
    return {
        f"maxSmoothed{side.title()}{joint.title()}AngleDeg": segment.max_angle_deg,
        f"smoothed{side.title()}{joint.title()}ExcursionDeg": segment.max_angle_deg
        - segment.min_angle_deg,
        "angleMeasurementStartMs": segment.angle_measurement_start_ms,
        f"timeToMin{joint.title()}AngleMs": segment.bottom_ms - segment.start_ms,
        f"timeFromMin{joint.title()}AngleMs": segment.end_ms - segment.bottom_ms,
    }
