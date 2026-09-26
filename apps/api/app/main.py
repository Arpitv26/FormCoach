from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import coach, health, live, videos
from app.core.config import get_settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="FormCoach API",
        version="0.1.0",
        description=(
            "Push-up and squat counting from supplied poses. Form scoring and video CV are pending."
        ),
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(get_settings().cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    for router in (health.router, live.router, videos.router, coach.router):
        app.include_router(router, prefix="/api/v1")
    return app


app = create_app()
