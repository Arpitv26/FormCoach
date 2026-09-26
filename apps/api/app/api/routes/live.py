from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.analysis.exercises.registry import PROFILES
from app.analysis.interfaces import MovementAnalyzer
from app.analysis.placeholder import PlaceholderAnalyzer
from app.domain.analysis import AnalysisResponse, Source
from app.domain.models import ErrorResponse
from app.domain.pose import LiveBatchRequest

router = APIRouter()


def get_analyzer() -> MovementAnalyzer:
    return PlaceholderAnalyzer()


@router.post(
    "/live/analyze-batch",
    response_model=AnalysisResponse,
    responses={400: {"model": ErrorResponse}},
    tags=["analysis"],
)
def analyze_batch(
    request: LiveBatchRequest,
    analyzer: Annotated[MovementAnalyzer, Depends(get_analyzer)],
) -> AnalysisResponse:
    profile = PROFILES.get(request.exercise_hint) if request.exercise_hint else None
    if request.exercise_hint and profile is None:
        raise HTTPException(
            400,
            detail={
                "code": "UNKNOWN_EXERCISE",
                "message": "Use an exercise ID from docs/API_CONTRACT.md.",
            },
        )
    return analyzer.analyze(
        request.frames,
        session_id=request.session_id,
        source=Source(
            type="live", duration_ms=(request.frames[-1].timestamp_ms if request.frames else None)
        ),
        image_width=request.image_width,
        image_height=request.image_height,
        profile=profile,
        is_final=request.is_final,
    )
