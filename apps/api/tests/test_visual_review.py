"""Visual interpretations are separate, timestamp-grounded and optional."""

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.domain.analysis import AnalysisResponse
from app.domain.models import CoachRequest
from app.domain.visual_review import VisualFinding, VisualReview
from app.services import visual_review as service
from app.services.coach_evidence import evidence_cards
from app.services.conversation_coach import ConversationReply, conversation_evidence, converse

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def analysis():
    a = AnalysisResponse.model_validate_json(
        (ROOT / "contracts/examples/pushup-comparison-analysis.json").read_text()
    )
    a.source.type = "upload"
    return a


def review():
    return VisualReview(
        status="complete",
        model="test-model",
        sampled_timestamps_ms=[0, 500, 1000],
        findings=[
            VisualFinding(
                kind="adjustment",
                observation="Torso rocks between positions.",
                cue="Keep your torso steadier on the next pull.",
                evidence_timestamps_ms=[0, 1000],
            )
        ],
        limitations=["Sampled frames only."],
    )


@pytest.mark.parametrize("change", ["invented_time", "duplicate_time", "unordered", "unavailable"])
def test_review_rejects_unsupported_timestamps_and_failure_claims(change):
    data = review().model_dump()
    if change == "invented_time":
        data["findings"][0]["evidence_timestamps_ms"] = [0, 777]
    elif change == "duplicate_time":
        data["findings"][0]["evidence_timestamps_ms"] = [0, 0]
    elif change == "unordered":
        data["sampled_timestamps_ms"] = [500, 0, 1000]
    else:
        data["status"] = "unavailable"
    with pytest.raises(ValidationError):
        VisualReview.model_validate(data)


def test_analysis_checks_visual_timeline_and_upload_origin(analysis):
    data = analysis.model_dump()
    data["visual_review"] = review().model_dump()
    data["source"]["type"] = "live"
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(data)
    data["source"] = {"type": "upload", "duration_ms": 100}
    with pytest.raises(ValidationError):
        AnalysisResponse.model_validate(data)


def test_visual_cards_work_with_no_counted_reps_and_resolve_paths(analysis):
    analysis.visual_review = review()
    analysis.reps = []
    analysis.summary.total_reps = None
    analysis.status = "insufficient_data"
    cards = evidence_cards(analysis)
    visual = next(c for c in cards if c.id == "visual-1")
    assert "AI VISUAL INTERPRETATION" in visual.text
    for path in visual.paths:
        value = analysis.model_dump(by_alias=True)
        for item in path.split("."):
            value = value[int(item)] if isinstance(value, list) else value[item]
        assert value is not None


def test_sdk_gets_images_times_and_measurements_not_filename(analysis, monkeypatch):
    monkeypatch.setattr(service, "sample_video", lambda *_: [(0, "jpeg1"), (1000, "jpeg2")])
    received = {}

    class Client:
        def __init__(self, **kwargs):
            received["config"] = kwargs
            self.responses = SimpleNamespace(parse=self.parse)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def parse(self, **kwargs):
            received.update(kwargs)
            return SimpleNamespace(
                status="completed",
                output_parsed=service.ReviewDraft(
                    findings=[
                        service.DraftFinding(
                            kind="adjustment",
                            observation="Torso rocks.",
                            cue="Keep steady.",
                            evidence_frame_indices=[0, 1],
                        )
                    ],
                    limitations=[],
                ),
            )

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Client))
    result = service.OpenAIVisualReviewer(Settings((), "test-only")).review(
        Path("BadForm7reps.mov"), analysis
    )
    assert result.status == "complete"
    content = received["input"][0]["content"]
    assert len([c for c in content if c["type"] == "input_image"]) == 2
    assert "timestampMs=1000" in json.dumps(content)
    assert "BadForm" not in json.dumps(content) and "test-only" not in json.dumps(content)
    assert received["store"] is False
    # A human filename label cannot select or alter the review prompt.
    service.OpenAIVisualReviewer(Settings((), "test-only")).review(
        Path("GoodForm7reps.mov"), analysis
    )
    assert received["input"][0]["content"] == content
    # Different uploaded images, even under the same name, must produce different input.
    service.OpenAIVisualReviewer(Settings((), "test-only")).review(
        Path("GoodForm7reps.mov"), analysis, [(0, "different1"), (1000, "different2")]
    )
    changed = received["input"][0]["content"]
    assert changed != content
    assert "different1" in json.dumps(changed) and "jpeg1" not in json.dumps(changed)


def test_review_failure_preserves_measurements_and_does_not_log_secrets(
    analysis, monkeypatch, caplog
):
    original = analysis.model_dump()

    def fail(*_):
        raise RuntimeError("SECRET-KEY-AND-IMAGE")

    monkeypatch.setattr(service, "sample_video", fail)
    result = service.OpenAIVisualReviewer(Settings((), "test-only")).review(Path("x.mov"), analysis)
    assert result.status == "unavailable" and result.findings == []
    assert analysis.model_dump() == original
    assert "SECRET" not in caplog.text and "RuntimeError" in caplog.text


def test_sample_limit_rotation_timestamps_and_release(monkeypatch):
    class Capture:
        index = -1
        released = False

        def isOpened(self):
            return True

        def set(self, prop, value):
            assert (prop, value) == (1, 1)

        def read(self):
            self.index += 1
            return (True, SimpleNamespace(shape=(2160, 3840, 3)))

        def get(self, _):
            return self.index * 100

        def release(self):
            self.released = True

    capture = Capture()
    dimensions = []
    cv2 = SimpleNamespace(
        VideoCapture=lambda *_: capture,
        CAP_FFMPEG=0,
        CAP_PROP_ORIENTATION_AUTO=1,
        CAP_PROP_POS_MSEC=2,
        IMWRITE_JPEG_QUALITY=3,
        resize=lambda image, size: dimensions.append(size) or image,
        imencode=lambda *_: (True, b"jpeg"),
    )
    monkeypatch.setitem(sys.modules, "cv2", cv2)
    frames = service.sample_video(Path("x.mov"), 120000)
    assert len(frames) == 64 and capture.released
    assert frames[-1][0] <= 120000 and len(set(t for t, _ in frames)) == 64
    assert set(dimensions) == {(960, 540)}


def test_breakdown_gets_all_seven_reps_and_long_answer_is_allowed(analysis):
    template = analysis.reps[0]
    analysis.reps = [
        template.model_copy(
            update={
                "rep_number": i,
                "start_ms": i * 3000,
                "end_ms": i * 3000 + 1000,
                "key_moments": [],
                "issues": [],
            }
        )
        for i in range(1, 8)
    ]
    analysis.summary.total_reps = 7
    analysis.source.duration_ms = 24000
    analysis.timeline = []
    analysis.issues = []
    request = CoachRequest(analysis=analysis, mode="qa", question="Give me a breakdown of each rep")
    assert len([c for c in conversation_evidence(request) if c.id.endswith("-time")]) == 7
    reply = ConversationReply(
        message="Measured details. " * 150, kind="session", evidence_ids=["rep-1-time"]
    )
    result = asyncio.run(converse(request, SimpleNamespace(write=AsyncMock(return_value=reply))))
    assert result.provider == "openai"


def test_synthetic_visual_fixture_validates_and_is_explicitly_synthetic():
    from jsonschema import Draft202012Validator

    raw = json.loads((ROOT / "contracts/examples/visual-review-analysis.json").read_text())
    Draft202012Validator(
        json.loads((ROOT / "contracts/analysis.schema.json").read_text())
    ).validate(raw)
    a = AnalysisResponse.model_validate(raw)
    assert a.provenance.kind == "synthetic" and a.visual_review.status == "complete"
