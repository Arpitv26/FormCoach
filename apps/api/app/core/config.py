import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

API_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    openai_api_key: str = field(repr=False)


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
    )
