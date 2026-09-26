import pytest
from pydantic import ValidationError

from app.domain.video import PoseTrack


def test_synthetic_overlay_example_matches_both_contract_representations():
    import json
    from pathlib import Path

    from jsonschema import Draft202012Validator

    from app.domain.pose import LANDMARK_NAMES
    from app.domain.video import VideoAnalysisResponse

    root = Path(__file__).resolve().parents[3]
    payload = json.loads((root / "contracts/examples/pushup-video-with-pose.json").read_text())
    result = VideoAnalysisResponse.model_validate(payload)
    assert result.analysis.provenance.kind == "synthetic"
    bundle = json.loads((root / "contracts/api.schema.json").read_text())
    Draft202012Validator(
        {"$defs": bundle["$defs"], "$ref": "#/$defs/VideoAnalysisResponse"}
    ).validate(payload)
    # Browser adapter indices must retain the same anatomical names.
    names_source = (root / "apps/web/src/lib/pose/names.ts").read_text()
    names = json.loads(names_source.split("=", 1)[1].split(" as const;")[0])
    assert names == list(LANDMARK_NAMES)


def test_pose_track_temporal_bounds_and_dimensions():
    data = {
        "imageWidth": 1280,
        "imageHeight": 720,
        "durationMs": 100,
        "frames": [
            {"frameIndex": 0, "timestampMs": 0, "landmarks": []},
            {"frameIndex": 1, "timestampMs": 100, "landmarks": []},
        ],
    }
    assert len(PoseTrack.model_validate(data).frames) == 2
    for patch in (
        {"durationMs": 99},
        {"frames": data["frames"][::-1]},
        {"imageWidth": 4096, "imageHeight": 4096},
        {"frames": data["frames"] * 901},
    ):
        with pytest.raises(ValidationError):
            PoseTrack.model_validate(data | patch)
