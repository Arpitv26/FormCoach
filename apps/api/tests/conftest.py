import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(autouse=True)
def isolate_coach_credentials(monkeypatch):
    """Local .env credentials must never turn ordinary tests into paid API calls."""
    monkeypatch.setenv("COACH_PROVIDER", "fallback")
    monkeypatch.setenv("OPENAI_API_KEY", "")


@pytest.fixture
def client():
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def analysis_example():
    return json.loads((ROOT / "contracts/examples/squat-analysis.json").read_text())


@pytest.fixture
def live_example():
    return json.loads((ROOT / "contracts/examples/live-pose-batch.json").read_text())
