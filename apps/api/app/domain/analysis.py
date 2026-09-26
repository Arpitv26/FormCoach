"""Stable v1.0 analysis contract. None means unknown, never a score of zero."""

from typing import Literal, Self

from pydantic import Field, model_validator

from app.domain.base import Confidence, ContractModel, Milliseconds, Score


class Provenance(ContractModel):
    kind: Literal["measured", "synthetic", "placeholder"]
    label: str


class Source(ContractModel):
    type: Literal["live", "upload"]
    duration_ms: Milliseconds | None


class Exercise(ContractModel):
    id: str
    name: str
    confidence: Confidence | None


class CameraQuality(ContractModel):
    score: Confidence | None
    full_body_visible: bool | None
    issues: list[str]


class Summary(ContractModel):
    overall_score: Score | None
    total_reps: int | None = Field(ge=0)
    primary_focus: str | None
    headline: str


class RepMetrics(ContractModel):
    range_of_motion: Score | None
    symmetry: Score | None
    tempo: Score | None
    stability: Score | None


class SessionMetrics(RepMetrics):
    consistency: Score | None


class Issue(ContractModel):
    id: str
    code: str
    severity: Literal["low", "medium", "high"]
    confidence: Confidence | None
    title: str
    short_cue: str
    explanation: str
    start_ms: Milliseconds
    end_ms: Milliseconds
    involved_joints: list[str]

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.end_ms < self.start_ms:
            raise ValueError("Issue endMs must be at or after startMs")
        return self


class KeyMoment(ContractModel):
    timestamp_ms: Milliseconds
    type: str
    label: str


class RepAnalysis(ContractModel):
    rep_number: int = Field(ge=1)
    start_ms: Milliseconds
    end_ms: Milliseconds
    score: Score | None
    metrics: RepMetrics
    measurements: dict[str, float | None]
    issues: list[Issue]
    key_moments: list[KeyMoment]

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.end_ms <= self.start_ms:
            raise ValueError("Rep endMs must be after startMs")
        for moment in self.key_moments:
            if not self.start_ms <= moment.timestamp_ms <= self.end_ms:
                raise ValueError("Key moments must be inside their rep")
        return self


class TimelineEvent(ContractModel):
    timestamp_ms: Milliseconds
    type: Literal["rep_start", "rep_end", "key_moment", "issue"]
    rep_number: int | None = Field(ge=1)
    issue_id: str | None
    label: str


class ScoringInfo(ContractModel):
    version: str
    method: str
    weights: dict[str, Confidence]


class AnalysisResponse(ContractModel):
    contract_version: Literal["1.0"]
    session_id: str = Field(min_length=1, max_length=100)
    status: Literal["complete", "partial", "insufficient_data", "not_implemented"]
    provenance: Provenance
    source: Source
    exercise: Exercise | None
    camera_quality: CameraQuality
    summary: Summary
    metrics: SessionMetrics
    reps: list[RepAnalysis]
    issues: list[Issue]
    timeline: list[TimelineEvent]
    limitations: list[str]
    scoring: ScoringInfo | None

    @model_validator(mode="after")
    def validate_consistency(self) -> Self:
        if self.summary.total_reps is not None and self.summary.total_reps != len(self.reps):
            raise ValueError("totalReps must equal the number of completed reps")
        if [rep.rep_number for rep in self.reps] != list(range(1, len(self.reps) + 1)):
            raise ValueError("Rep numbers must be consecutive and start at 1")
        for previous, current in zip(self.reps, self.reps[1:], strict=False):
            if current.start_ms < previous.end_ms:
                raise ValueError("Reps must be chronological and non-overlapping")
        if self.timeline != sorted(self.timeline, key=lambda event: event.timestamp_ms):
            raise ValueError("Timeline must be chronological")
        issue_by_id = {issue.id: issue for issue in self.issues}
        if len(issue_by_id) != len(self.issues):
            raise ValueError("Session issue IDs must be unique")
        for rep in self.reps:
            for issue in rep.issues:
                if issue_by_id.get(issue.id) != issue:
                    raise ValueError("Rep issues must match an issue in the session list")
                if issue.end_ms < rep.start_ms or issue.start_ms > rep.end_ms:
                    raise ValueError("Rep issues must overlap their rep")
        for event in self.timeline:
            if event.rep_number is not None and event.rep_number > len(self.reps):
                raise ValueError("Timeline references an unknown rep")
            if event.issue_id is not None and event.issue_id not in issue_by_id:
                raise ValueError("Timeline references an unknown issue")
        duration = self.source.duration_ms
        endpoints = [rep.end_ms for rep in self.reps] + [issue.end_ms for issue in self.issues]
        endpoints += [event.timestamp_ms for event in self.timeline]
        if duration is not None and any(point > duration for point in endpoints):
            raise ValueError("Analysis timestamps must fit inside source.durationMs")
        if self.status in {"not_implemented", "insufficient_data"}:
            if self.summary.overall_score is not None or self.summary.total_reps is not None:
                raise ValueError("Unavailable analysis must not claim a score or rep count")
            if not self.limitations:
                raise ValueError("Unavailable analysis must explain why in limitations")
        return self
