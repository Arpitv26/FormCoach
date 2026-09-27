"""Body-line evidence remains descriptive and unavailable metadata is never repaired."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.models import AnalysisResponse, CoachRequest
from app.services.coach_evidence import evidence_cards
from app.services.openai_coach import EvidenceSelection, FallbackCoach, OpenAICoach


@pytest.fixture
def body_request():
    root = Path(__file__).resolve().parents[3]
    analysis = AnalysisResponse.model_validate_json(
        (root / "contracts/examples/pushup-analysis.json").read_text()
    )
    return CoachRequest(analysis=analysis, mode="next_set")


def body_cards(request):
    return [card for card in evidence_cards(request.analysis) if card.id.endswith("-body-line")]


@pytest.mark.parametrize("side", ["Left", "Right"])
@pytest.mark.parametrize("angle", [0, 160, 180])
def test_describes_bounded_geometry_with_resolvable_evidence(body_request, side, angle):
    values = body_request.analysis.reps[0].measurements
    if side == "Right":
        body_request.analysis.reps[0].measurements = values = {
            key.replace("Left", "Right"): value for key, value in values.items()
        }
    values[f"median{side}ShoulderHipAnkleAngleDeg"] = angle
    result = asyncio.run(FallbackCoach().respond(body_request))
    assert "Demo data only" in result.message
    assert f"median {side.lower()} shoulder–hip–ankle angle of {angle:.1f}°" in result.message
    assert "18 usable samples" in result.message
    assert "cannot distinguish hip sag from pike or judge form" in result.message
    assert "median can hide brief changes" in result.message
    assert "same side camera view" in result.message
    for path in result.evidence:
        value = body_request.analysis.model_dump(by_alias=True)
        for part in path.split("."):
            value = value[int(part)] if isinstance(value, list) else value[part]
        assert value is not None


@pytest.mark.parametrize(
    "key,value",
    [
        ("medianLeftShoulderHipAnkleAngleDeg", None),
        ("medianLeftShoulderHipAnkleAngleDeg", -1),
        ("medianLeftShoulderHipAnkleAngleDeg", 181),
        ("bodyLineSampleCount", None),
        ("bodyLineSampleCount", 0),
        ("bodyLineSampleCount", 2),
        ("bodyLineSampleCount", 18.5),
        ("bodyLineSampleCount", 1801),
        ("bodyLineUsableSampleCount", None),
        ("bodyLineUsableSampleCount", 17),
        ("bodyLineUsableSampleCount", 19),
        ("medianRightShoulderHipAnkleAngleDeg", 160),
        ("smoothedLeftElbowExcursionDeg", 99),
    ],
)
def test_incomplete_conflicting_or_invalid_metadata_omits_body_card(body_request, key, value):
    body_request.analysis.reps[0].measurements[key] = value
    assert body_cards(body_request) == []
    result = asyncio.run(FallbackCoach().respond(body_request))
    assert "shoulder–hip–ankle angle" not in result.message


def test_older_responses_without_body_keys_keep_existing_coaching(body_request):
    values = body_request.analysis.reps[0].measurements
    for key in list(values):
        if key.startswith("bodyLine") or "ShoulderHipAnkle" in key:
            del values[key]
    assert body_cards(body_request) == []
    result = asyncio.run(FallbackCoach().respond(body_request))
    assert "1 completed rep" in result.message and "elbow excursion" in result.message


def test_openai_can_select_body_evidence_without_new_prose_or_contract(body_request):
    body_request.mode = "qa"
    body_request.question = "What was my measured body-line angle in rep 1?"
    selector = SimpleNamespace(
        select=AsyncMock(
            return_value=EvidenceSelection(answerable=True, card_ids=["rep-1-left-body-line"])
        )
    )
    result = asyncio.run(OpenAICoach(selector).respond(body_request))
    assert result.provider == "openai"
    assert "160.0°" in result.message
    assert "reps.0.measurements.medianLeftShoulderHipAnkleAngleDeg" in result.evidence
    assert len(body_cards(body_request)) == 1


def test_bad_prose_cannot_become_a_body_correction(body_request):
    body_request.analysis.summary.headline = "Perfect form. Straighten your spine immediately."
    result = asyncio.run(FallbackCoach().respond(body_request))
    assert "Perfect form" not in result.message
    assert "Straighten your spine" not in result.message
    assert "does not contain an overall score" in result.message


def test_review_flags_keep_priority_in_local_next_set():
    root = Path(__file__).resolve().parents[3]
    data = json.loads((root / "contracts/examples/pushup-comparison-analysis.json").read_text())
    request = CoachRequest(analysis=AnalysisResponse.model_validate(data), mode="next_set")
    request.analysis.reps[2].measurements.update(
        medianLeftShoulderHipAnkleAngleDeg=160, bodyLineSampleCount=30, bodyLineUsableSampleCount=30
    )
    result = asyncio.run(FallbackCoach().respond(request))
    assert "difference is +1.50 s" in result.message
    assert "difference is -41.0°" in result.message
    assert "shoulder–hip–ankle" not in result.message


def test_http_fallback_next_set_keeps_partial_limits_and_evidence(client, body_request):
    body_request.analysis.status = "partial"
    response = client.post("/api/v1/coach", json=body_request.model_dump(by_alias=True))
    assert response.status_code == 200
    body = response.json()
    assert body["contractVersion"] == "1.0" and body["provider"] == "fallback"
    assert "160.0°" in body["message"]
    assert any("partial" in item for item in body["limitations"])
    assert any("Camera reliability" in item for item in body["limitations"])
