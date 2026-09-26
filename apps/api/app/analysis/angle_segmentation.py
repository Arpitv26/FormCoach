"""Conservative rep segmentation from one consistently selected joint angle.

All thresholds are uncalibrated hackathon heuristics. This is not exercise recognition,
a form assessment, or a guarantee that a camera view supports the measurement.
"""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from statistics import median

from app.analysis.rep_segmentation import (
    AngleSample,
    MovementPhase,
    RepSegment,
    SegmentationResult,
)


@dataclass(frozen=True)
class AngleCycleConfig:
    extended_angle_deg: float = 160
    flexed_angle_deg: float = 100
    hysteresis_deg: float = 10
    minimum_phase_ms: int = 150
    minimum_rep_ms: int = 800
    maximum_rep_ms: int = 15_000
    maximum_gap_ms: int = 300
    smoothing_window: int = 3

    def __post_init__(self) -> None:
        angles = (self.flexed_angle_deg, self.extended_angle_deg, self.hysteresis_deg)
        if not all(isfinite(value) for value in angles) or not (
            0
            <= self.flexed_angle_deg
            < self.flexed_angle_deg + self.hysteresis_deg
            < self.extended_angle_deg - self.hysteresis_deg
            < self.extended_angle_deg
            <= 180
        ):
            raise ValueError("Angle thresholds must define separated bottom and extension zones")
        durations = (
            self.minimum_phase_ms,
            self.minimum_rep_ms,
            self.maximum_rep_ms,
            self.maximum_gap_ms,
        )
        if any(type(value) is not int or value <= 0 for value in durations):
            raise ValueError("Time thresholds must be positive integer milliseconds")
        if self.maximum_rep_ms <= self.minimum_rep_ms:
            raise ValueError("maximum_rep_ms must exceed minimum_rep_ms")
        if (
            type(self.smoothing_window) is not int
            or self.smoothing_window < 1
            or (self.smoothing_window % 2 == 0)
        ):
            raise ValueError("smoothing_window must be a positive odd integer")


class _AngleCycleCounter:
    """One replay's local state. Never shared between HTTP requests or sessions."""

    def __init__(self, config: AngleCycleConfig) -> None:
        self.config = config
        self.reps: list[RepSegment] = []
        self.phase: MovementPhase = "unknown"
        self.window: deque[float] = deque(maxlen=config.smoothing_window)
        self.last_angle: float | None = None
        self.previous_timestamp: int | None = None
        self.tracking_breaks = 0
        self.candidate: MovementPhase | None = None
        self.candidate_since = 0
        self.start_ms: int | None = None
        self.bottom_ms = 0
        self.min_angle = 180.0
        self.max_angle = 0.0
        self.angle_measurement_start_ms = 0

    def _reset(self) -> None:
        self.phase = "unknown"
        self.window.clear()
        self.last_angle = None
        self.candidate = None
        self.start_ms = None

    def update(self, sample: AngleSample) -> None:
        timestamp = sample.timestamp_ms
        gap = self.previous_timestamp is not None and (
            timestamp - self.previous_timestamp > self.config.maximum_gap_ms
        )
        if gap:
            if self.window:
                self.tracking_breaks += 1
            self._reset()
        self.previous_timestamp = timestamp
        if sample.angle_deg is None:
            if self.window:
                self.tracking_breaks += 1
            self._reset()
            return

        if self.start_ms is not None and timestamp - self.start_ms > self.config.maximum_rep_ms:
            self._reset()
        self.window.append(sample.angle_deg)
        # Require a full window after startup/tracking loss; never fill it with guessed samples.
        if len(self.window) < self.config.smoothing_window:
            return
        self.last_angle = float(median(self.window))
        if self.start_ms is not None and self.last_angle < self.min_angle:
            self.min_angle = self.last_angle
            self.bottom_ms = timestamp
        if self.start_ms is not None:
            self.max_angle = max(self.max_angle, self.last_angle)

        target = self._target(self.last_angle)
        if target is None:
            self.candidate = None
            return
        if target != self.candidate:
            self.candidate = target
            self.candidate_since = timestamp
        elif timestamp - self.candidate_since >= self.config.minimum_phase_ms:
            self._transition(target, timestamp)
            # This same observation may already satisfy the next phase's threshold
            # (e.g. the arm is extended when ascent is confirmed). Start its dwell
            # now; waiting for another frame adds a needless sample of latency.
            self.candidate = self._target(self.last_angle)
            self.candidate_since = timestamp

    def _target(self, angle: float) -> MovementPhase | None:
        config = self.config
        if self.phase == "unknown":
            return "extended" if angle >= config.extended_angle_deg else None
        if self.phase == "extended":
            return "descent" if angle <= config.extended_angle_deg - config.hysteresis_deg else None
        if self.phase == "descent":
            if angle >= config.extended_angle_deg:
                return "extended"  # Shallow attempt: return to ready without counting.
            return "bottom" if angle <= config.flexed_angle_deg else None
        if self.phase == "bottom":
            return "ascent" if angle >= config.flexed_angle_deg + config.hysteresis_deg else None
        if angle >= config.extended_angle_deg:
            return "extended"
        return "bottom" if angle <= config.flexed_angle_deg else None

    def _transition(self, target: MovementPhase, timestamp: int) -> None:
        if target == "descent":
            self.start_ms = self.candidate_since
            self.min_angle = self.last_angle
            self.max_angle = self.last_angle
            self.angle_measurement_start_ms = timestamp
            self.bottom_ms = timestamp
        elif target == "extended":
            if (
                self.phase == "ascent"
                and self.start_ms is not None
                and (timestamp - self.start_ms >= self.config.minimum_rep_ms)
            ):
                self.reps.append(
                    RepSegment(
                        self.start_ms,
                        self.bottom_ms,
                        timestamp,
                        self.min_angle,
                        self.max_angle,
                        self.angle_measurement_start_ms,
                    )
                )
            self.start_ms = None
        self.phase = target


def segment_angle_cycles(
    samples: Sequence[AngleSample],
    *,
    config: AngleCycleConfig | None = None,
) -> SegmentationResult:
    """Replay a whole cumulative set. Return completed reps; never finalize a partial rep.

    Use one anatomical side throughout the set. Any unavailable angle resets readiness
    and the unfinished rep. A gap over maximum_gap_ms does the same. After either, stable
    extension must be observed again. Completed reps survive these resets.

    Boundaries use observed timestamps of the causal smoothed signal: start is the first
    sample of a confirmed descent; end confirms extension; bottom is the earliest observed
    minimum after descent confirmation. Angle extrema cover that confirmation through
    completion, inclusive. Smoothing/confirmation add latency. No interpolation.
    """
    for previous, current in zip(samples, samples[1:], strict=False):
        if current.timestamp_ms <= previous.timestamp_ms:
            raise ValueError("Angle sample timestamps must strictly increase")
    counter = _AngleCycleCounter(config or AngleCycleConfig())
    for sample in samples:
        counter.update(sample)
    return SegmentationResult(
        tuple(counter.reps),
        counter.phase,
        counter.last_angle,
        counter.tracking_breaks,
    )
