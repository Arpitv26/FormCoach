"""Upload analysis and its normalized playback pose track."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.domain.analysis import AnalysisResponse
from app.domain.base import ContractModel
from app.domain.pose import PoseFrame


class PoseTrack(ContractModel):
    image_width: int = Field(ge=1, le=4096)
    image_height: int = Field(ge=1, le=4096)
    duration_ms: int = Field(ge=0, le=120_000)
    frames: list[PoseFrame] = Field(max_length=1800)

    @model_validator(mode="after")
    def validate_timeline(self) -> Self:
        if self.image_width * self.image_height > 3840 * 2160:
            raise ValueError("Pose track exceeds 4K image area")
        for previous, current in zip(self.frames, self.frames[1:], strict=False):
            if (
                current.frame_index <= previous.frame_index
                or current.timestamp_ms <= previous.timestamp_ms
            ):
                raise ValueError("Pose track indices and timestamps must strictly increase")
        if self.frames and self.frames[-1].timestamp_ms > self.duration_ms:
            raise ValueError("Pose frame exceeds clip duration")
        return self


class VideoAnalysisResponse(ContractModel):
    contract_version: Literal["1.0"] = "1.0"
    analysis: AnalysisResponse
    pose_track: PoseTrack

    @model_validator(mode="after")
    def matching_source(self) -> Self:
        if self.analysis.source.type != "upload":
            raise ValueError("Video analysis requires an uploaded source")
        if self.analysis.source.duration_ms != self.pose_track.duration_ms:
            raise ValueError("Analysis and pose track must describe the same duration")
        return self
