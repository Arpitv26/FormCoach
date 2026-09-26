from fastapi import APIRouter

from app.core.config import get_settings
from app.domain.models import CoachRequest, CoachResponse
from app.services.openai_coach import get_coach_service

router = APIRouter()


@router.post("/coach", response_model=CoachResponse, tags=["coach"])
async def coach(request: CoachRequest) -> CoachResponse:
    return await get_coach_service(get_settings()).respond(request)
