"""Model-authored visual observations, explicitly separate from geometric measurements."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.domain.base import ContractModel


class VisualFinding(ContractModel):
    kind: Literal["adjustment", "positive", "observation"]
    phase: Literal["exercise", "setup", "finish"] = "exercise"
    observation: str = Field(min_length=1, max_length=500)
    cue: str = Field(min_length=1, max_length=300)
    evidence_timestamps_ms: list[int] = Field(min_length=2, max_length=8)


class VisualReview(ContractModel):
    status: Literal["complete", "unavailable"]
    source: Literal["openai_sampled_frames"] = "openai_sampled_frames"
    model: str = Field(max_length=100)
    sampled_timestamps_ms: list[int] = Field(max_length=64)
    findings: list[VisualFinding] = Field(max_length=8)
    limitations: list[str] = Field(max_length=8)

    @model_validator(mode="after")
    def valid_evidence(self) -> Self:
        times = self.sampled_timestamps_ms
        if times != sorted(set(times)) or any(not 0 <= t <= 120000 for t in times):
            raise ValueError("Visual sample times must increase within the video limit")
        if self.status == "unavailable" and self.findings:
            raise ValueError("Unavailable review cannot contain findings")
        if self.status == "complete" and len(times) < 2:
            raise ValueError("Visual review needs multiple frames")
        for finding in self.findings:
            cited = finding.evidence_timestamps_ms
            if len(set(cited)) != len(cited) or not set(cited).issubset(times):
                raise ValueError("Visual findings must cite distinct supplied frames")
        return self
