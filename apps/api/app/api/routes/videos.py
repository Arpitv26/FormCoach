from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.domain.analysis import AnalysisResponse
from app.domain.models import ErrorResponse
from app.services.video_processor import PlaceholderVideoProcessor

router = APIRouter()


@router.post(
    "/videos/analyze",
    response_model=AnalysisResponse,
    responses={501: {"model": ErrorResponse}},
    tags=["analysis"],
)
async def analyze_video(
    file: Annotated[UploadFile, File()],
    exercise_hint: Annotated[str | None, Form(alias="exerciseHint", max_length=50)] = None,
) -> AnalysisResponse:
    try:
        return await PlaceholderVideoProcessor().analyze(file, exercise_hint)
    except NotImplementedError as error:
        raise HTTPException(
            501,
            detail={
                "code": "VIDEO_ANALYSIS_NOT_IMPLEMENTED",
                "message": str(error),
            },
        ) from error
    finally:
        await file.close()
