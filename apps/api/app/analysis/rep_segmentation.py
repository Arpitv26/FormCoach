"""Internal time-series inputs and completed-rep boundaries; no HTTP contract changes."""

from dataclasses import dataclass
from math import isfinite
from typing import Literal

type MovementPhase = Literal["unknown", "standing", "descent", "bottom", "ascent"]


@dataclass(frozen=True)
class AngleSample:
    timestamp_ms: int
    angle_deg: float | None

    def __post_init__(self) -> None:
        if type(self.timestamp_ms) is not int or self.timestamp_ms < 0:
            raise ValueError("Sample timestamps must be nonnegative integer milliseconds")
        if self.angle_deg is not None and (
            not isfinite(self.angle_deg) or not 0 <= self.angle_deg <= 180
        ):
            raise ValueError("Angles must be finite degrees between 0 and 180, or None")


@dataclass(frozen=True)
class RepSegment:
    start_ms: int
    bottom_ms: int
    end_ms: int
    min_angle_deg: float


@dataclass(frozen=True)
class SegmentationResult:
    reps: tuple[RepSegment, ...]
    current_phase: MovementPhase
    last_smoothed_angle_deg: float | None
    tracking_breaks: int
