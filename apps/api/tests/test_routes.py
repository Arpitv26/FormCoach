import pytest

from app.domain.analysis import AnalysisResponse
from app.domain.models import CoachResponse


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "formcoach-api"}


def test_browser_origin_is_allowed(client):
    response = client.options(
        "/api/v1/live/analyze-batch",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_live_returns_honest_unknowns_and_is_repeatable(client, live_example):
    response = client.post("/api/v1/live/analyze-batch", json=live_example)
    assert response.status_code == 200
    analysis = AnalysisResponse.model_validate(response.json())
    assert analysis.status == "insufficient_data"
    assert analysis.provenance.kind == "measured"
    assert analysis.summary.overall_score is None
    assert analysis.summary.total_reps is None
    assert analysis.exercise.confidence is None
    assert not analysis.reps and not analysis.issues
    assert analysis.session_id == live_example["sessionId"]
    assert response.json() == client.post("/api/v1/live/analyze-batch", json=live_example).json()


def test_empty_frames_and_unknown_hint(client, live_example):
    live_example["frames"] = []
    live_example["exerciseHint"] = None
    response = client.post("/api/v1/live/analyze-batch", json=live_example)
    assert response.status_code == 200
    assert response.json()["source"]["durationMs"] is None
    assert response.json()["exercise"] is None
    live_example["exerciseHint"] = "universal-magic"
    assert client.post("/api/v1/live/analyze-batch", json=live_example).status_code == 400


@pytest.mark.parametrize("mutation", ["order", "name", "duplicate", "version", "dimensions"])
def test_live_rejects_invalid_batches(client, live_example, mutation):
    if mutation == "order":
        live_example["frames"].reverse()
    elif mutation == "name":
        live_example["frames"][0]["landmarks"][0]["name"] = "left_knee"
    elif mutation == "duplicate":
        live_example["frames"][0]["landmarks"].append(live_example["frames"][0]["landmarks"][0])
    elif mutation == "version":
        live_example["contractVersion"] = "2.0"
    else:
        live_example["imageWidth"] = 0
    assert client.post("/api/v1/live/analyze-batch", json=live_example).status_code == 422


def test_coach_fallback_without_key(client, analysis_example, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    response = client.post("/api/v1/coach", json={"analysis": analysis_example, "mode": "summary"})
    assert response.status_code == 200
    coach = CoachResponse.model_validate(response.json())
    assert coach.provider == "fallback"
    assert "Demo data only" in coach.message
    assert "81/100" in coach.message
    assert coach.evidence == ["summary.overallScore"]


def test_coach_does_not_invent_findings_for_unavailable_analysis(client, live_example):
    analysis = client.post("/api/v1/live/analyze-batch", json=live_example).json()
    response = client.post("/api/v1/coach", json={"analysis": analysis, "mode": "next_set"})
    assert response.status_code == 200
    assert response.json()["evidence"] == []
    assert "not enough measured analysis" in response.json()["message"]


def test_coach_qa_requires_question_and_admits_limits(client, analysis_example):
    request = {"analysis": analysis_example, "mode": "qa"}
    assert client.post("/api/v1/coach", json=request).status_code == 422
    request["question"] = "What should I improve?"
    response = client.post("/api/v1/coach", json=request)
    assert response.status_code == 200
    assert "not supported" in response.json()["message"]
