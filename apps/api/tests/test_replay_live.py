"""Test the capture checker with the real route and synthetic inputs, plus transport failures."""

import json
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest
from test_live_analysis import CYCLE, STANDING, squat_request

from app.domain.analysis import AnalysisResponse
from app.domain.pose import LiveBatchRequest
from app.tools import replay_live


def test_checked_in_example_is_explicitly_synthetic_and_replays(client):
    path = Path(__file__).resolve().parents[1] / "examples/synthetic-pushup-capture.json"
    capture = replay_live.load_capture(path)
    assert capture.session_id == "synthetic-one-pushup-not-camera-data"
    report = replay_live.replay_capture(capture, transport(client), expected_reps=1)
    assert report["outcome"] == "count_match"
    rep = report["analysis"]["reps"][0]
    assert (rep["startMs"], rep["endMs"]) == (500, 2100)
    assert rep["keyMoments"][0]["timestampMs"] == 1100
    assert rep["measurements"]["minSmoothedLeftElbowAngleDeg"] == pytest.approx(90)


def transport(client):
    def send(batch):
        response = client.post(
            "/api/v1/live/analyze-batch", json=batch.model_dump(mode="json", by_alias=True)
        )
        assert response.status_code == 200
        return AnalysisResponse.model_validate(response.json())

    return send


@pytest.mark.parametrize("batch_size", [1, 7, 15, 1800])
def test_replays_real_route_in_batches_without_mutating_capture(client, batch_size):
    capture = LiveBatchRequest.model_validate(squat_request(STANDING + CYCLE * 3))
    original = capture.model_dump()
    batches = []

    def send(batch):
        batches.append(batch)
        return transport(client)(batch)

    report = replay_live.replay_capture(capture, send, expected_reps=3, batch_frames=batch_size)
    assert report["outcome"] == "count_match"
    assert report["countMatches"]
    assert report["observedReps"] == 3
    assert report["cumulativeRepsStable"] and report["finalReplayIdentical"]
    assert report["analysis"]["summary"]["overallScore"] is None
    assert all(not batch.is_final for batch in batches[:-2])
    assert batches[-1] == batches[-2]
    assert batches[-1].is_final
    assert batches[-1].frames == capture.frames
    assert capture.model_dump() == original


def test_count_mismatch_is_a_result_not_silent_success(client):
    capture = LiveBatchRequest.model_validate(squat_request())
    report = replay_live.replay_capture(capture, transport(client), expected_reps=2)
    assert report["outcome"] == "count_mismatch"
    assert not report["countMatches"]
    assert (report["expectedReps"], report["observedReps"]) == (2, 1)


def test_partial_with_matching_count_still_needs_review(client):
    request = squat_request()
    request["frames"][-1]["landmarks"] = []
    capture = LiveBatchRequest.model_validate(request)
    report = replay_live.replay_capture(capture, transport(client), expected_reps=1)
    assert report["outcome"] == "incomplete_analysis"
    assert report["countMatches"]
    assert report["analysis"]["status"] == "partial"


@pytest.mark.parametrize("mutation", ["session", "coverage", "exercise", "changed_rep", "repeat"])
def test_inconsistent_server_responses_fail_loudly(client, mutation):
    capture = LiveBatchRequest.model_validate(squat_request(STANDING + CYCLE * 2))
    calls = 0

    def send(batch):
        nonlocal calls
        calls += 1
        result = transport(client)(batch)
        if mutation == "session":
            result.session_id = "wrong-session"
        elif mutation == "coverage":
            result.source.duration_ms = 9999
        elif mutation == "exercise":
            result.exercise.id = "lunge"
        elif mutation == "changed_rep" and calls == 2:
            result.reps[0].measurements["durationMs"] += 100
        elif mutation == "repeat" and calls == 3:
            result.summary.headline = "Different response on repeat"
        return result

    with pytest.raises(replay_live.ReplayError):
        replay_live.replay_capture(capture, send, expected_reps=2, batch_frames=25)


@pytest.mark.parametrize("bad_capture", ["empty", "wrong_hint", "malformed", "order", "oversized"])
def test_rejects_invalid_capture_before_sending(tmp_path, monkeypatch, bad_capture):
    request = squat_request()
    if bad_capture == "empty":
        request["frames"] = []
    elif bad_capture == "wrong_hint":
        request["exerciseHint"] = "lunge"
    elif bad_capture == "order":
        request["frames"].reverse()
    elif bad_capture == "oversized":
        monkeypatch.setattr(replay_live, "MAX_CAPTURE_BYTES", 10)
    path = tmp_path / "capture.json"
    path.write_text("not JSON" if bad_capture == "malformed" else json.dumps(request))
    with pytest.raises(ValueError):
        replay_live.load_capture(path)


@pytest.mark.parametrize(
    "options", [{"expected_reps": -1}, {"batch_frames": 0}, {"batch_frames": 1801}]
)
def test_bad_options_never_send_requests(options):
    capture = LiveBatchRequest.model_validate(squat_request())

    def send(_batch):
        pytest.fail("Invalid options must fail before sending")

    with pytest.raises(ValueError):
        replay_live.replay_capture(capture, send, **{"expected_reps": 1, **options})


def test_http_transport_sends_aliases_and_final_flag(client, monkeypatch):
    batch = LiveBatchRequest.model_validate(squat_request(final=True))
    result = transport(client)(batch)

    def urlopen(request, timeout):
        assert request.full_url == "http://localhost:8000/api/v1/live/analyze-batch"
        assert request.method == "POST" and timeout == 15
        assert json.loads(request.data) == batch.model_dump(mode="json", by_alias=True)
        return BytesIO(result.model_dump_json(by_alias=True).encode())

    monkeypatch.setattr(replay_live, "urlopen", urlopen)
    assert replay_live.post_batch("http://localhost:8000/", batch) == result


@pytest.mark.parametrize(
    "error",
    [URLError("offline"), TimeoutError(), HTTPError("http://localhost", 422, "invalid", {}, None)],
)
def test_http_failures_have_actionable_errors(monkeypatch, error):
    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(replay_live, "urlopen", fail)
    with pytest.raises(replay_live.ReplayError, match="API"):
        replay_live.post_batch(
            "http://localhost:8000", LiveBatchRequest.model_validate(squat_request())
        )


@pytest.mark.parametrize("expected,exit_code", [(1, 0), (2, 1)])
def test_cli_outputs_report_and_meaningful_exit_code(
    client, tmp_path, monkeypatch, capsys, expected, exit_code
):
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(squat_request()))
    monkeypatch.setattr(replay_live, "post_batch", lambda _url, batch: transport(client)(batch))
    assert replay_live.main([str(path), "--expected-reps", str(expected)]) == exit_code
    report = json.loads(capsys.readouterr().out)
    assert report["observedReps"] == 1
    assert report["expectedReps"] == expected


def test_cli_missing_file_explains_failure(tmp_path, capsys):
    assert replay_live.main([str(tmp_path / "missing.json"), "--expected-reps", "1"]) == 2
    assert "Replay failed" in capsys.readouterr().err


def test_cli_invalid_json_does_not_dump_capture_contents(tmp_path, capsys):
    path = tmp_path / "invalid.json"
    path.write_text('{"private_capture_marker":')
    assert replay_live.main([str(path), "--expected-reps", "1"]) == 2
    output = capsys.readouterr()
    assert "Invalid capture" in output.err
    assert "private_capture_marker" not in output.err
