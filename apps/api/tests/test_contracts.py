import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from app.domain.analysis import AnalysisResponse
from app.domain.pose import LiveBatchRequest

ROOT = Path(__file__).resolve().parents[3]


def test_examples_validate_with_python_and_json_schema(analysis_example, live_example):
    AnalysisResponse.model_validate(analysis_example)
    LiveBatchRequest.model_validate(live_example)
    schema = json.loads((ROOT / "contracts/analysis.schema.json").read_text())
    Draft202012Validator(schema).validate(analysis_example)
    bundle = json.loads((ROOT / "contracts/api.schema.json").read_text())
    live_schema = {"$defs": bundle["$defs"], "$ref": "#/$defs/LiveBatchRequest"}
    Draft202012Validator(live_schema).validate(live_example)


def test_demo_score_arithmetic_and_worst_rep(analysis_example):
    analysis = AnalysisResponse.model_validate(analysis_example)
    weights = analysis.scoring.weights
    rep_weights = {key: value for key, value in weights.items() if key != "consistency"}
    for rep in analysis.reps:
        metrics = rep.metrics.model_dump(by_alias=True)
        expected = round(
            sum(metrics[key] * weight for key, weight in rep_weights.items())
            / sum(rep_weights.values()),
            1,
        )
        assert rep.score == pytest.approx(expected)
    metrics = analysis.metrics.model_dump(by_alias=True)
    for key in rep_weights:
        mean = round(
            sum(rep.metrics.model_dump(by_alias=True)[key] for rep in analysis.reps) / 6, 1
        )
        assert metrics[key] == pytest.approx(mean)
    scores = [rep.score for rep in analysis.reps]
    assert metrics["consistency"] == pytest.approx(round(100 - (max(scores) - min(scores)), 1))
    expected = round(sum(metrics[key] * weight for key, weight in weights.items()), 1)
    assert analysis.summary.overall_score == pytest.approx(expected)
    assert min(analysis.reps, key=lambda rep: rep.score).rep_number == 5


@pytest.mark.parametrize("mutation", ["score", "reps", "duration", "issue", "timeline"])
def test_inconsistent_analysis_is_rejected(analysis_example, mutation):
    if mutation == "score":
        analysis_example["summary"]["overallScore"] = 150
    elif mutation == "reps":
        analysis_example["summary"]["totalReps"] = 7
    elif mutation == "duration":
        analysis_example["source"]["durationMs"] = 100
    elif mutation == "issue":
        analysis_example["issues"][0]["id"] = "mismatched-id"
    else:
        analysis_example["timeline"].reverse()
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(analysis_example)
