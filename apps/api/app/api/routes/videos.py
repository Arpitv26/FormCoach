import logging
from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.analysis.movement import RuleBasedAnalyzer
from app.core.config import get_settings
from app.domain.analysis import AnalysisResponse
from app.domain.models import ErrorResponse
from app.domain.video import VideoAnalysisResponse
from app.services.mediapipe_pose import (
    MediaPipePoseProvider,
    VideoInputError,
    VideoProcessingTimeout,
    VideoSetupError,
)
from app.services.video_processor import UploadedVideoProcessor, VideoProcessor, VideoRequestError

router = APIRouter()
logger = logging.getLogger(__name__)


@lru_cache
def get_video_processor() -> VideoProcessor:
    from app.services.visual_review import OpenAIVisualReviewer

    settings = get_settings()
    review_enabled = bool(
        settings.visual_review_enabled
        and settings.coach_provider == "openai"
        and settings.openai_api_key.strip()
    )
    return UploadedVideoProcessor(
        MediaPipePoseProvider(settings.pose_model_path, include_visual_frames=review_enabled),
        RuleBasedAnalyzer(),
        OpenAIVisualReviewer(settings) if review_enabled else None,
        gym_provider=MediaPipePoseProvider(
            settings.pose_model_path, include_visual_frames=review_enabled, allow_dominant_pose=True
        ),
    )


@router.post(
    "/videos/analyze",
    response_model=AnalysisResponse,
    responses={status: {"model": ErrorResponse} for status in (400, 413, 415, 500, 503, 504)},
    tags=["analysis"],
)
def analyze_video(
    file: Annotated[UploadFile, File()],
    processor: Annotated[VideoProcessor, Depends(get_video_processor)],
    exercise_hint: Annotated[str | None, Form(alias="exerciseHint", max_length=50)] = None,
) -> AnalysisResponse:
    return _process_upload(file, lambda: processor.analyze(file, exercise_hint))


@router.post(
    "/videos/analyze-with-pose",
    response_model=VideoAnalysisResponse,
    responses={status: {"model": ErrorResponse} for status in (400, 413, 415, 500, 503, 504)},
    tags=["analysis"],
)
def analyze_video_with_pose(
    file: Annotated[UploadFile, File()],
    processor: Annotated[VideoProcessor, Depends(get_video_processor)],
    exercise_hint: Annotated[str | None, Form(alias="exerciseHint", max_length=50)] = None,
) -> VideoAnalysisResponse:
    return _process_upload(file, lambda: processor.analyze_with_pose(file, exercise_hint))


def _process_upload[T](file: UploadFile, operation: Callable[[], T]) -> T:
    # FastAPI runs synchronous routes in its worker pool, keeping health/live responsive.
    try:
        return operation()
    except VideoRequestError as error:
        raise HTTPException(
            error.status, detail={"code": error.code, "message": str(error)}
        ) from error
    except VideoSetupError as error:
        raise HTTPException(
            503, detail={"code": "VIDEO_SETUP_REQUIRED", "message": str(error)}
        ) from error
    except VideoProcessingTimeout as error:
        raise HTTPException(
            504, detail={"code": "VIDEO_PROCESSING_TIMEOUT", "message": str(error)}
        ) from error
    except VideoInputError as error:
        raise HTTPException(400, detail={"code": "INVALID_VIDEO", "message": str(error)}) from error
    except Exception as error:
        logger.exception("Video processing failed")
        raise HTTPException(
            500,
            detail={
                "code": "VIDEO_PROCESSING_FAILED",
                "message": "Processing failed. Check the API terminal and try a shorter clip.",
            },
        ) from error
    finally:
        file.file.close()
