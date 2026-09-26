"""Descriptive 2D observations; no target tempo, quality score, or form judgment."""

from app.analysis.rep_segmentation import RepSegment


def pushup_measurements(segment: RepSegment, side: str) -> dict[str, float | int]:
    """Use the counter's causal signal/window, never resmooth individual cropped reps.

    Extrema cover confirmed descent through completion (both endpoints included).
    The minimum moment is the first occurrence of the exact lowest smoothed angle.
    Timing partitions the counted interval at that moment; it includes dwell/pauses.
    """
    return {
        f"maxSmoothed{side.title()}ElbowAngleDeg": segment.max_angle_deg,
        f"smoothed{side.title()}ElbowExcursionDeg": segment.max_angle_deg - segment.min_angle_deg,
        "angleMeasurementStartMs": segment.angle_measurement_start_ms,
        "timeToMinElbowAngleMs": segment.bottom_ms - segment.start_ms,
        "timeFromMinElbowAngleMs": segment.end_ms - segment.bottom_ms,
    }
