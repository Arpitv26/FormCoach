import logging
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.analysis.movement import RuleBasedAnalyzer
from app.core.config import get_settings
from app.domain.analysis import AnalysisResponse
from app.domain.models import ErrorResponse
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
    return UploadedVideoProcessor(
        MediaPipePoseProvider(get_settings().pose_model_path), RuleBasedAnalyzer()
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
    # FastAPI runs synchronous routes in its worker pool, keeping health/live responsive.
    try:
        return processor.analyze(file, exercise_hint)
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
