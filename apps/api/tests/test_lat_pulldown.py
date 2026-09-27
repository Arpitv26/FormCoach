"""Synthetic mechanics and HTTP integration, not independent camera validation."""

from copy import deepcopy

import pytest
from test_live_analysis import analyze
from test_pushup_analysis import pushup_request

from app.analysis.exercises.lat_pulldown import LAT_PULLDOWN_PROFILE
from app.analysis.movement import RuleBasedAnalyzer
from app.domain.analysis import Source
from app.domain.models import CoachRequest
from app.domain.pose import LiveBatchRequest
from app.services.coach_evidence import evidence_cards
from app.services.conversation_coach import local_reply
from app.services.pose_provider import PoseSequence
from app.tools import analyze_video

READY = [150] * 5
CYCLE = [110] * 4 + [50] * 6 + [90] * 4 + READY


def lat_request(angles=None, **kwargs):
    request = pushup_request(READY + CYCLE * 3 if angles is None else angles, **kwargs)
    return {**request, "exerciseHint": "lat-pulldown"}


@pytest.mark.parametrize("side", ["left", "right"])
def test_counts_lat_cycles_and_explains_correct_exercise(client, side):
    result = analyze(client, lat_request(side=side, final=True))
    assert result.summary.total_reps == 3
    assert result.status == "complete"
    assert result.exercise.id == "lat-pulldown"
    assert result.exercise.confidence is None
    assert result.summary.overall_score is None
    assert result.movement_observations == [] and result.issues == []
    assert result.reps[0].measurements[f"smoothed{side.title()}ElbowExcursionDeg"] == pytest.approx(
        100
    )
    cards = evidence_cards(result, preferred_reps=(3,))
    assert any(card.id == "rep-3-time" for card in cards)
    assert any("lat pulldown" in card.text for card in cards)
    assert all("body-line" not in card.id for card in cards)
    reply = local_reply(CoachRequest(analysis=result, mode="summary"))
    assert "3 completed reps" in reply.message
    assert "push-up" not in reply.message


@pytest.mark.parametrize(
    "angles, count",
    [
        ([], None),
        ([50] * 30, None),
        (READY, 0),
        (READY + [100] * 8 + READY, 0),
        (READY + [110] * 4 + [50] * 6, 0),
        (READY + [110] * 8 + [50] + [110] * 8 + READY, 0),
        (READY + [110] * 4 + [50] * 70 + [90] * 4 + READY, 1),
    ],
)
def test_unknown_holds_shallow_spikes_and_unfinished(client, angles, count):
    assert analyze(client, lat_request(angles, final=True)).summary.total_reps == count


@pytest.mark.parametrize("failure", ["missing", "visibility", "outside", "gap"])
def test_tracking_loss_discards_unfinished_rep_without_switching_sides(client, failure):
    request = lat_request(READY + CYCLE * 2, final=True)
    right = lat_request(READY + CYCLE * 2, side="right")
    for frame, other in zip(request["frames"], right["frames"], strict=True):
        frame["landmarks"] += other["landmarks"]
    for broken in request["frames"][33:36]:
        if failure == "missing":
            broken["landmarks"] = broken["landmarks"][3:]
        elif failure == "visibility":
            broken["landmarks"][1]["visibility"] = None
        elif failure == "outside":
            broken["landmarks"][1]["x"] = 1.1
    if failure == "gap":
        for frame in request["frames"][33:]:
            frame["timestampMs"] += 301
    result = analyze(client, request)
    assert result.summary.total_reps == 1
    assert result.status == "partial"


def test_cumulative_replay_and_upload_use_identical_reps(client):
    request = lat_request(final=True)
    original = deepcopy(request)
    previous = []
    for end in range(1, len(request["frames"]) + 1):
        result = analyze(client, {**request, "frames": request["frames"][:end], "isFinal": False})
        assert result.reps[: len(previous)] == previous
        previous = result.reps
    capture = LiveBatchRequest.model_validate(request)
    upload = RuleBasedAnalyzer().analyze(
        capture.frames,
        session_id=capture.session_id,
        source=Source(type="upload", duration_ms=capture.frames[-1].timestamp_ms),
        image_width=capture.image_width,
        image_height=capture.image_height,
        profile=LAT_PULLDOWN_PROFILE,
        is_final=True,
    )
    assert upload.reps == previous
    assert request == original


def test_cli_preserves_explicit_exercise_in_both_files(tmp_path, monkeypatch):
    capture = LiveBatchRequest.model_validate(lat_request(final=True))
    sequence = PoseSequence(
        capture.frames, capture.image_width, capture.image_height, capture.frames[-1].timestamp_ms
    )
    monkeypatch.setattr(analyze_video.MediaPipePoseProvider, "extract", lambda *_: sequence)
    output = tmp_path / "lat"
    assert (
        analyze_video.main(["fake.mov", "--exercise", "lat-pulldown", "--output", str(output)]) == 0
    )
    saved = LiveBatchRequest.model_validate_json((output / "poses.json").read_text())
    assert saved.exercise_hint == "lat-pulldown"
    assert '"lat-pulldown"' in (output / "analysis.json").read_text()


def test_multipart_lat_upload_returns_matching_pose_track_and_coach(client):
    from app.api.routes.videos import get_video_processor
    from app.services.video_processor import UploadedVideoProcessor

    capture = LiveBatchRequest.model_validate(lat_request(final=True))
    sequence = PoseSequence(capture.frames, 1280, 720, capture.frames[-1].timestamp_ms)

    class Provider:
        def extract(self, path):
            assert path.read_bytes() == b"synthetic video"
            return sequence

    processor = UploadedVideoProcessor(Provider(), RuleBasedAnalyzer())
    client.app.dependency_overrides[get_video_processor] = lambda: processor
    try:
        result = client.post(
            "/api/v1/videos/analyze-with-pose",
            files={"file": ("lat.mov", b"synthetic video", "video/quicktime")},
            data={"exerciseHint": "lat-pulldown"},
        )
        assert result.status_code == 200
        body = result.json()
        assert body["analysis"]["summary"]["totalReps"] == 3
        assert body["analysis"]["exercise"]["id"] == "lat-pulldown"
        assert body["poseTrack"]["frames"] == capture.model_dump(by_alias=True)["frames"]
        coach = client.post(
            "/api/v1/coach",
            json={"analysis": body["analysis"], "mode": "summary", "responseStyle": "conversation"},
        )
        assert coach.status_code == 200
        assert "push-up" not in coach.json()["message"]
    finally:
        client.app.dependency_overrides.pop(get_video_processor)


def test_short_gap_preserves_observed_phases_without_filling_missing_extrema(client):
    request = lat_request(READY + CYCLE * 2, final=True)
    request["frames"][33]["landmarks"] = []
    result = analyze(client, request)
    assert result.summary.total_reps == 2 and result.status == "partial"
    assert result.reps[1].measurements["maxSmoothedLeftElbowAngleDeg"] == pytest.approx(150)
