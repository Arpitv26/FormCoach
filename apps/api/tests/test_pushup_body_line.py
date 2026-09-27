"""Known image-plane geometry and gaps; not a form-quality benchmark."""

import json
from copy import deepcopy
from math import cos, radians, sin
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from test_live_analysis import CYCLE, STANDING, analyze
from test_pushup_analysis import pushup_request

from app.analysis.exercises.pushup_body_line import add_body_line_measurements
from app.domain.analysis import AnalysisResponse
from app.domain.pose import LANDMARK_NAMES, PoseFrame


def body_request(angles=None, *, side="left", body_angle=160, final=True):
    request = pushup_request(angles, side=side, final=final)
    for frame in request["frames"]:
        # Shoulder (500,200), hip (500,350), ankle 150 pixels from hip.
        for joint, x, y in (
            ("hip", 500, 350),
            ("ankle", 500 + 150 * sin(radians(body_angle)), 350 - 150 * cos(radians(body_angle))),
        ):
            name = f"{side}_{joint}"
            frame["landmarks"].append(
                dict(
                    index=LANDMARK_NAMES.index(name),
                    name=name,
                    x=x / 1280,
                    y=y / 720,
                    visibility=0.9,
                )
            )
    return request


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("angle", [0, 90, 160, 180])
def test_known_body_angle_and_sample_counts_without_quality_claim(client, side, angle):
    result = analyze(client, body_request(side=side, body_angle=angle))
    rep = result.reps[0]
    assert rep.measurements[f"median{side.title()}ShoulderHipAnkleAngleDeg"] == pytest.approx(angle)
    assert rep.measurements["bodyLineSampleCount"] == 17
    assert rep.measurements["bodyLineUsableSampleCount"] == 17
    assert (rep.start_ms, rep.end_ms) == (500, 2100)
    assert result.summary.total_reps == 1
    assert rep.score is None and result.summary.overall_score is None
    assert result.issues == [] and result.scoring is None
    assert result.camera_quality.full_body_visible is None


@pytest.mark.parametrize(
    "width,height,mirror", [(720, 1280, False), (640, 640, False), (1280, 720, True)]
)
def test_aspect_ratio_and_mirroring_preserve_body_angle(client, width, height, mirror):
    request = body_request(body_angle=145)
    for frame in request["frames"]:
        for point in frame["landmarks"]:
            point["x"] *= 0.5 * 1280 / width
            point["y"] *= 0.5 * 720 / height
            if mirror:
                point["x"] = 1 - point["x"]
    request.update(imageWidth=width, imageHeight=height)
    result = analyze(client, request)
    assert result.reps[0].measurements["medianLeftShoulderHipAnkleAngleDeg"] == pytest.approx(145)


@pytest.mark.parametrize("failure", ["missing", "unknown", "low", "outside", "degenerate"])
def test_one_unavailable_body_sample_nulls_median_but_keeps_elbow_rep(client, failure):
    request = body_request()
    baseline = analyze(client, request)
    hip = request["frames"][12]["landmarks"][-2]
    if failure == "missing":
        request["frames"][12]["landmarks"].remove(hip)
    elif failure == "unknown":
        hip["visibility"] = None
    elif failure == "low":
        hip["visibility"] = 0.69
    elif failure == "outside":
        hip["x"] = -0.01
    else:
        hip["x"], hip["y"] = 500 / 1280, 200 / 720
    result = analyze(client, request)
    m = result.reps[0].measurements
    assert m["medianLeftShoulderHipAnkleAngleDeg"] is None
    assert m["bodyLineSampleCount"] == 17 and m["bodyLineUsableSampleCount"] == 16
    assert result.timeline == baseline.timeline
    assert result.summary == baseline.summary and result.status == baseline.status
    assert (
        result.reps[0].measurements["minSmoothedLeftElbowAngleDeg"]
        == baseline.reps[0].measurements["minSmoothedLeftElbowAngleDeg"]
    )


def test_no_side_switch_and_each_rep_recovers_independently(client):
    request = body_request(STANDING + CYCLE * 2)
    right = body_request(STANDING + CYCLE * 2, side="right")
    for frame, other in zip(request["frames"], right["frames"], strict=True):
        frame["landmarks"].extend(other["landmarks"])
    request["frames"][12]["landmarks"][3]["visibility"] = 0
    result = analyze(client, request)
    assert result.reps[0].measurements["medianLeftShoulderHipAnkleAngleDeg"] is None
    assert result.reps[1].measurements["medianLeftShoulderHipAnkleAngleDeg"] == pytest.approx(160)
    assert all("medianRightShoulderHipAnkleAngleDeg" not in rep.measurements for rep in result.reps)


def test_median_ignores_outside_window_and_is_stable_under_cumulative_replay(client):
    request = body_request(STANDING + CYCLE * 2)
    alternate = body_request(STANDING + CYCLE * 2, body_angle=90)
    # One inside-window outlier; every other change is outside rep 1.
    for index in [*range(5), 12, *range(22, 45)]:
        request["frames"][index]["landmarks"][-1] = alternate["frames"][index]["landmarks"][-1]
    original = deepcopy(request)
    first = analyze(client, {**request, "frames": request["frames"][:24], "isFinal": False})
    full = analyze(client, request)
    assert full.reps[0] == first.reps[0]
    assert full.reps[0].measurements["medianLeftShoulderHipAnkleAngleDeg"] == pytest.approx(160)
    assert full.reps[1].measurements["medianLeftShoulderHipAnkleAngleDeg"] == pytest.approx(90)
    assert request == original


@pytest.mark.parametrize("indices", [[], [5, 21], [6, 7, 21], [5, 6, 20], [5, 6, 21]])
def test_sparse_or_missing_boundaries_are_not_summarized(client, indices):
    request = body_request()
    reps = analyze(client, request).reps
    before = deepcopy(reps)
    frames = [PoseFrame.model_validate(request["frames"][i]) for i in indices]
    result = add_body_line_measurements(
        reps, frames, side="left", image_width=1280, image_height=720, minimum_visibility=0.7
    )
    assert result[0].measurements["medianLeftShoulderHipAnkleAngleDeg"] is None
    assert result[0].measurements["bodyLineUsableSampleCount"] == len(indices)
    assert reps == before


def test_fixture_body_values_match_authored_geometry_and_existing_schema(client):
    root = Path(__file__).resolve().parents[3]
    fixture = json.loads((root / "contracts/examples/pushup-analysis.json").read_text())
    AnalysisResponse.model_validate(fixture)
    Draft202012Validator(
        json.loads((root / "contracts/analysis.schema.json").read_text())
    ).validate(fixture)
    # The fixture has an authored interval, not the current counter's boundary policy.
    actual = add_body_line_measurements(
        AnalysisResponse.model_validate(fixture).reps,
        [PoseFrame.model_validate(frame) for frame in body_request()["frames"]],
        side="left",
        image_width=1280,
        image_height=720,
        minimum_visibility=0.7,
    )
    for key in (
        "bodyLineSampleCount",
        "bodyLineUsableSampleCount",
        "medianLeftShoulderHipAnkleAngleDeg",
    ):
        assert fixture["reps"][0]["measurements"][key] == pytest.approx(actual[0].measurements[key])
    assert fixture["provenance"]["kind"] == "synthetic"
