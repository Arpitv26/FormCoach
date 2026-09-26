"""Provider-independent, unmirrored image coordinates. See API_CONTRACT.md."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.domain.base import Confidence, ContractModel, Milliseconds

LANDMARK_NAMES = (
    "nose",
    "left_eye_inner",
    "left_eye",
    "left_eye_outer",
    "right_eye_inner",
    "right_eye",
    "right_eye_outer",
    "left_ear",
    "right_ear",
    "mouth_left",
    "mouth_right",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_pinky",
    "right_pinky",
    "left_index",
    "right_index",
    "left_thumb",
    "right_thumb",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
    "left_heel",
    "right_heel",
    "left_foot_index",
    "right_foot_index",
)


class PoseLandmark(ContractModel):
    index: int = Field(ge=0, le=32)
    name: str
    # Out-of-frame coordinates may exceed [0, 1]; do not clamp them into view.
    x: float
    y: float
    z: float | None = None
    visibility: Confidence | None = None

    @model_validator(mode="after")
    def validate_name(self) -> Self:
        if self.name != LANDMARK_NAMES[self.index]:
            raise ValueError("Landmark index and canonical name must match")
        return self


class PoseFrame(ContractModel):
    frame_index: int = Field(ge=0)
    timestamp_ms: Milliseconds
    landmarks: list[PoseLandmark] = Field(max_length=33)

    @model_validator(mode="after")
    def validate_unique_landmarks(self) -> Self:
        indices = [landmark.index for landmark in self.landmarks]
        if len(indices) != len(set(indices)):
            raise ValueError("Each landmark index may occur only once per frame")
        return self


class LiveBatchRequest(ContractModel):
    contract_version: Literal["1.0"] = "1.0"
    session_id: str = Field(min_length=1, max_length=100)
    exercise_hint: str | None = Field(default=None, max_length=50)
    # Cumulative snapshot, not deltas: see the stateless batching protocol in the docs.
    frames: list[PoseFrame] = Field(max_length=1800)
    is_final: bool = False
    image_width: int = Field(gt=0, le=16384)
    image_height: int = Field(gt=0, le=16384)

    @model_validator(mode="after")
    def validate_frame_order(self) -> Self:
        for previous, current in zip(self.frames, self.frames[1:], strict=False):
            if (
                current.frame_index <= previous.frame_index
                or current.timestamp_ms <= previous.timestamp_ms
            ):
                raise ValueError("Frame indices and timestamps must strictly increase")
        if self.frames and self.frames[-1].timestamp_ms > 120_000:
            raise ValueError("Bootstrap live sessions are limited to 120000 ms")
        return self
