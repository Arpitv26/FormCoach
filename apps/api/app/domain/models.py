"""Request/response envelopes used by routes and schema generation."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.domain.analysis import AnalysisResponse
from app.domain.base import ContractModel
from app.domain.pose import LiveBatchRequest
from app.domain.video import VideoAnalysisResponse


class HealthResponse(ContractModel):
    status: Literal["ok"]
    service: Literal["formcoach-api"]


class CoachRequest(ContractModel):
    analysis: AnalysisResponse
    mode: Literal["summary", "next_set", "qa"]
    question: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def require_qa_question(self) -> Self:
        if self.mode == "qa" and (not self.question or not self.question.strip()):
            raise ValueError("A non-empty question is required for qa mode")
        return self


class CoachResponse(ContractModel):
    contract_version: Literal["1.0"]
    session_id: str
    mode: Literal["summary", "next_set", "qa"]
    provider: Literal["fallback", "openai"]
    message: str
    evidence: list[str]
    limitations: list[str]


class ErrorDetail(ContractModel):
    code: str
    message: str


class ErrorResponse(ContractModel):
    detail: ErrorDetail


class ApiContract(ContractModel):
    """Schema bundle for generating matching frontend types; not an API endpoint."""

    analysis_response: AnalysisResponse
    video_analysis_response: VideoAnalysisResponse
    live_batch_request: LiveBatchRequest
    coach_request: CoachRequest
    coach_response: CoachResponse
    health_response: HealthResponse
    error_response: ErrorResponse
