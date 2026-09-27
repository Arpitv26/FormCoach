"""Declared review expectations use the real route, without retiming captured poses."""

import json

import pytest
from test_pushup_comparisons import flagged_request
from test_replay_live import transport

from app.domain.pose import LiveBatchRequest
from app.tools.replay_live import DURATION_CODE, EXCURSION_CODE, main, replay_capture


def test_synthetic_positive_replay_checks_both_rules_and_keeps_input(client):
    capture = LiveBatchRequest.model_validate(flagged_request())
    original = capture.model_dump()
    report = replay_capture(
        capture,
        transport(client),
        expected_reps=3,
        expected_duration_change_reps=[3],
        expected_excursion_reduction_reps=[3],
    )
    assert report["outcome"] == "count_match"
    assert report["cumulativeRepsStable"] and report["finalReplayIdentical"]
    for code in (DURATION_CODE, EXCURSION_CODE):
        assert report["comparisonChecks"][code] == {
            "expectedReps": [3],
            "observedReps": [3],
            "missingReps": [],
            "unexpectedReps": [],
            "matches": True,
        }
    assert capture.model_dump() == original


@pytest.mark.parametrize("expected,missing,unexpected", [([], [], [3]), ([4], [4], [3])])
def test_reports_extra_and_missing_flags_independently_of_count(
    client, expected, missing, unexpected
):
    request = flagged_request()
    # A second copy of the changed cycle gives rep 4, without two stable reference durations.
    extra = request["frames"][-35:]
    request["frames"] += [
        {
            **frame,
            "frameIndex": frame["frameIndex"] + 35,
            "timestampMs": frame["timestampMs"] + 3500,
        }
        for frame in extra
    ]
    report = replay_capture(
        LiveBatchRequest.model_validate(request),
        transport(client),
        expected_reps=4,
        expected_duration_change_reps=expected,
    )
    assert report["countMatches"] and report["observedReps"] == 4
    assert report["outcome"] == "comparison_mismatch"
    check = report["comparisonChecks"][DURATION_CODE]
    assert check["missingReps"] == missing and check["unexpectedReps"] == unexpected
    assert not check["matches"]
    assert EXCURSION_CODE not in report["comparisonChecks"]


def test_omitted_expectations_do_not_assert_zero_flags(client):
    report = replay_capture(
        LiveBatchRequest.model_validate(flagged_request()),
        transport(client),
        expected_reps=3,
    )
    assert report["outcome"] == "count_match" and report["comparisonChecks"] == {}
    assert len(report["analysis"]["issues"]) == 2


@pytest.mark.parametrize("expected", [[0], [1], [2], [4], [3, 3], [3.0], [True]])
def test_invalid_expectations_fail_before_network(expected):
    def send(_):
        pytest.fail("Invalid expectation must fail before sending")

    with pytest.raises(ValueError, match="Expected flag reps"):
        replay_capture(
            LiveBatchRequest.model_validate(flagged_request()),
            send,
            expected_reps=3,
            expected_duration_change_reps=expected,
        )


def test_comparison_expectations_reject_other_exercises_before_network():
    capture = LiveBatchRequest.model_validate(flagged_request())
    capture.exercise_hint = "squat"
    with pytest.raises(ValueError, match="push-up capture"):
        replay_capture(
            capture,
            lambda _: pytest.fail("Unexpected send"),
            expected_reps=3,
            expected_excursion_reduction_reps=[],
        )


@pytest.mark.parametrize("partial", [True, False])
def test_count_or_incomplete_failure_keeps_priority(client, partial):
    request = flagged_request()
    if partial:
        request["frames"][-1]["landmarks"] = []
    report = replay_capture(
        LiveBatchRequest.model_validate(request),
        transport(client),
        expected_reps=4,
        expected_duration_change_reps=[],
    )
    assert report["outcome"] == ("incomplete_analysis" if partial else "count_mismatch")
    assert not report["comparisonChecks"][DURATION_CODE]["matches"]


@pytest.mark.parametrize("flags,exit_code", [(["3"], 0), ([], 1)])
def test_cli_empty_option_asserts_zero_and_mismatch_exits_one(
    client,
    tmp_path,
    monkeypatch,
    capsys,
    flags,
    exit_code,
):
    path = tmp_path / "synthetic.json"
    path.write_text(json.dumps(flagged_request()))
    monkeypatch.setattr(
        "app.tools.replay_live.post_batch", lambda _url, batch: transport(client)(batch)
    )
    assert (
        main([str(path), "--expected-reps", "3", "--expected-duration-change-reps", *flags])
        == exit_code
    )
    report = json.loads(capsys.readouterr().out)
    assert report["comparisonChecks"][DURATION_CODE]["expectedReps"] == [int(n) for n in flags]
