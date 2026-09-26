from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.domain.pose import PoseFrame


@dataclass(frozen=True)
class PoseSequence:
    frames: list[PoseFrame]
    image_width: int
    image_height: int
    duration_ms: int


class PoseProvider(Protocol):
    def extract(self, video_path: Path) -> PoseSequence:
        """Future adapter maps a pretrained provider into FormCoach domain landmarks."""
        ...
