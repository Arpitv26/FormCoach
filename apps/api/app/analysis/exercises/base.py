"""Exercise configuration is separate from the replaceable analysis algorithm."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class ExerciseProfile:
    id: str
    name: str
    relevant_joints: tuple[str, ...]
    camera_orientation: str
    phases: tuple[str, ...]
    metrics: tuple[str, ...]
    rules: tuple[str, ...]
    coaching_cues: tuple[str, ...]
    minimum_visibility: float = 0.7
    thresholds: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)
    status: Literal["example", "planned"] = "planned"
    calibration_note: str = "Hackathon heuristics; not clinically validated or calibrated."
