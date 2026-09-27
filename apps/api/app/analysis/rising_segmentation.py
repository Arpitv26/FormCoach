"""Causal low-to-high angle intervals; no interpolation or exercise recognition."""

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from statistics import median

from app.analysis.rep_segmentation import AngleSample, RepSegment, SegmentationResult


@dataclass(frozen=True)
class RisingConfig:
    ready_angle_deg: float
    target_angle_deg: float
    hysteresis_deg: float = 10
    minimum_phase_ms: int = 100
    minimum_rep_ms: int = 300
    maximum_rep_ms: int = 15000
    maximum_gap_ms: int = 300
    maximum_missing_ms: int = 0
    minimum_cycle_ms: int = 0

    def __post_init__(self):
        if (
            type(self.maximum_missing_ms) is not int
            or not 0 <= self.maximum_missing_ms <= self.maximum_gap_ms
        ):
            raise ValueError("Missing-data grace must be within the maximum gap")
        if (
            type(self.minimum_cycle_ms) is not int
            or not 0 <= self.minimum_cycle_ms <= self.maximum_rep_ms
        ):
            raise ValueError("Cycle interval must be within the maximum rep duration")
        if not all(
            isfinite(x) for x in (self.ready_angle_deg, self.target_angle_deg, self.hysteresis_deg)
        ) or not (
            0
            <= self.ready_angle_deg
            < self.ready_angle_deg + self.hysteresis_deg
            < self.target_angle_deg
            <= 180
        ):
            raise ValueError("Rising-angle zones must be finite, separated and within 0–180")
        if (
            any(
                type(x) is not int or x <= 0
                for x in (
                    self.minimum_phase_ms,
                    self.minimum_rep_ms,
                    self.maximum_rep_ms,
                    self.maximum_gap_ms,
                )
            )
            or self.maximum_rep_ms <= self.minimum_rep_ms
        ):
            raise ValueError("Positive time limits and maximum > minimum are required")


def segment_rising_angles(
    samples: Sequence[AngleSample], *, config: RisingConfig
) -> SegmentationResult:
    """Require a confirmed low zone before each rise; publish at confirmed high zone.

    The interval starts at the first observation in the confirmed low run. Angle extrema
    begin at low-position confirmation. Median confirmation and raw dwell are both required.
    After completion, lowering only rearms. Missing data resets an unfinished rise unless
    the profile enables bounded grace; grace retains phase, never median/dwell evidence.
    Completed intervals survive. Internal bottom/top names describe low/high signal zones.
    """
    for before, after in zip(samples, samples[1:], strict=False):
        if after.timestamp_ms <= before.timestamp_ms:
            raise ValueError("Angle sample timestamps must strictly increase")
    window = deque(maxlen=3)
    phase = "unknown"
    reps = []
    previous = None
    last_usable = None
    last = None
    zones = {}
    start = None
    minimum = maximum = bottom_ms = measurement_start = 0
    breaks = 0
    for sample in samples:
        timestamp, raw = sample.timestamp_ms, sample.angle_deg
        missing_gap = (
            last_usable is not None and timestamp - last_usable > config.maximum_missing_ms
        )
        if raw is None and config.maximum_missing_ms and not missing_gap:
            if window:
                breaks += 1
            window.clear()
            zones.clear()
            last = None
            previous = timestamp
            continue
        gap = previous is not None and timestamp - previous > config.maximum_gap_ms
        if config.maximum_missing_ms and not window and last_usable is not None and missing_gap:
            gap = True
        expired = start is not None and timestamp - start > config.maximum_rep_ms
        previous = timestamp
        if raw is None or gap or expired:
            if window and (raw is None or gap):
                breaks += 1
            window.clear()
            phase, last, start = "unknown", None, None
            zones.clear()
            if raw is None:
                continue
        last_usable = timestamp
        window.append(raw)
        if len(window) < 3:
            continue
        last = float(median(window))
        conditions = {
            "ready": raw <= config.ready_angle_deg,
            "rising": raw >= config.ready_angle_deg + config.hysteresis_deg,
            "target": raw >= config.target_angle_deg,
        }
        for zone, condition in conditions.items():
            if condition:
                zones.setdefault(zone, timestamp)
            else:
                zones.pop(zone, None)
        confirmed = {
            zone for zone, since in zones.items() if timestamp - since >= config.minimum_phase_ms
        }
        if phase in {"unknown", "top"}:
            if "ready" in confirmed and last <= config.ready_angle_deg:
                phase = "bottom"
                start = zones["ready"]
                measurement_start = bottom_ms = timestamp
                minimum = maximum = last
            continue
        if last < minimum:
            minimum, bottom_ms = last, timestamp
        maximum = max(maximum, last)
        if phase == "bottom":
            if "rising" not in confirmed or last < config.ready_angle_deg + config.hysteresis_deg:
                continue
            phase = "ascent"
        if phase == "ascent":
            if "ready" in confirmed and last <= config.ready_angle_deg:
                phase = "bottom"  # Incomplete rise, no manufactured rep.
                start = zones["ready"]
                measurement_start = bottom_ms = timestamp
                minimum = maximum = last
                continue
            if "target" in confirmed and last >= config.target_angle_deg:
                if timestamp - start >= config.minimum_rep_ms and (
                    not reps or timestamp - reps[-1].end_ms >= config.minimum_cycle_ms
                ):
                    reps.append(
                        RepSegment(start, bottom_ms, timestamp, minimum, maximum, measurement_start)
                    )
                phase, start = "top", None
    return SegmentationResult(tuple(reps), phase, last, breaks)
