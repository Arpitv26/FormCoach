import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    openai_api_key: str = field(repr=False)
    pose_model_path: Path = API_ROOT / "artifacts/models/pose_landmarker_full.task"
    coach_provider: str = "fallback"
    openai_model: str = "gpt-4.1-mini-2025-04-14"
    visual_review_enabled: bool = False
    openai_vision_model: str = "gpt-5.4-2026-03-05"


def get_settings() -> Settings:
    load_dotenv(API_ROOT / ".env")
    return Settings(
        cors_origins=tuple(
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            ).split(",")
            if origin.strip()
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        coach_provider=os.getenv("COACH_PROVIDER", "fallback"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini-2025-04-14"),
        visual_review_enabled=os.getenv("VISUAL_REVIEW_ENABLED", "false").lower() == "true",
        openai_vision_model=os.getenv("OPENAI_VISION_MODEL", "gpt-5.4-2026-03-05"),
        pose_model_path=API_ROOT
        / os.getenv("POSE_MODEL_PATH", "artifacts/models/pose_landmarker_full.task"),
    )
