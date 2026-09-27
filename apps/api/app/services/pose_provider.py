from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from app.domain.pose import PoseFrame


@dataclass(frozen=True)
class PoseSequence:
    frames: list[PoseFrame]
    image_width: int
    image_height: int
    duration_ms: int
    visual_frames: list[tuple[int, str]] = field(default_factory=list, repr=False)


class PoseProvider(Protocol):
    def extract(self, video_path: Path) -> PoseSequence:
        """Map pretrained provider output into FormCoach domain landmarks."""
        ...
