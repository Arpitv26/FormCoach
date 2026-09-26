"""Adapter boundary tests use fake decoding/inference; native smoke is run separately."""

import json
import sys
from types import SimpleNamespace as NS

import pytest
from test_pushup_analysis import pushup_request

from app.domain.pose import LANDMARK_NAMES, LiveBatchRequest
from app.services import mediapipe_pose as video
from app.services.pose_provider import PoseSequence
from app.tools import analyze_video


def points():
    return [NS(x=0.5, y=0.4, z=-0.1, visibility=0.9) for _ in LANDMARK_NAMES]


def test_landmark_adapter_preserves_names_coordinates_and_unknown_visibility():
    pose = points()
    pose[13].x = 1.1
    pose[13].visibility = None
    mapped = video.map_landmarks([pose])
    assert len(mapped) == 33
    assert [point.name for point in mapped] == list(LANDMARK_NAMES)
    assert mapped[13].x == 1.1 and mapped[13].visibility is None
    assert mapped[0].z == -0.1


@pytest.mark.parametrize("poses", [[], [points(), points()]])
def test_no_pose_and_multiple_people_are_unknown(poses):
    assert video.map_landmarks(poses) == []


def test_unexpected_landmark_layout_is_rejected():
    with pytest.raises(video.VideoInputError, match="33"):
        video.map_landmarks([points()[:10]])


@pytest.fixture
def adapter(tmp_path, monkeypatch):
    path = tmp_path / "test.mp4"
    path.write_bytes(b"fake decoding input")
    model = tmp_path / "test.task"
    model.write_bytes(b"fake model")
    state = NS(
        times=[0, 33, 67, 100, 134, 167],
        shapes=[(720, 1280, 3)] * 6,
        cursor=0,
        released=False,
        closed=False,
        detected=[],
        declared=6,
        rotation=0,
        auto=True,
        opened=True,
        poses=[points()],
        sar=(1, 1),
    )

    class Capture:
        def isOpened(self):
            return state.opened

        def get(self, key):
            values = {
                "count": state.declared,
                "time": state.times[max(0, state.cursor - 1)],
                "rotation": state.rotation,
                "auto": state.auto,
                "sar_num": state.sar[0],
                "sar_den": state.sar[1],
            }
            return values[key]

        def set(self, _key, _value):
            return state.auto

        def read(self):
            if state.cursor >= len(state.times):
                return False, None
            frame = NS(shape=state.shapes[state.cursor])
            state.cursor += 1
            return True, frame

        def release(self):
            state.released = True

    class Detector:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            state.closed = True

        def detect_for_video(self, _image, timestamp):
            state.detected.append(timestamp)
            return NS(pose_landmarks=state.poses)

    cv = NS(
        VideoCapture=lambda *_args: Capture(),
        CAP_FFMPEG=1,
        CAP_PROP_OPEN_TIMEOUT_MSEC=2,
        CAP_PROP_READ_TIMEOUT_MSEC=3,
        CAP_PROP_FRAME_COUNT="count",
        CAP_PROP_POS_MSEC="time",
        CAP_PROP_ORIENTATION_META="rotation",
        CAP_PROP_ORIENTATION_AUTO="auto",
        CAP_PROP_SAR_NUM="sar_num",
        CAP_PROP_SAR_DEN="sar_den",
        COLOR_BGR2RGB=4,
        cvtColor=lambda image, _: image,
    )
    mp = NS(
        Image=lambda **kwargs: kwargs,
        ImageFormat=NS(SRGB=1),
        tasks=NS(
            BaseOptions=lambda **kwargs: kwargs,
            vision=NS(
                PoseLandmarkerOptions=lambda **kwargs: kwargs,
                RunningMode=NS(VIDEO=1),
                PoseLandmarker=NS(create_from_options=lambda _options: Detector()),
            ),
        ),
    )
    monkeypatch.setitem(sys.modules, "cv2", cv)
    monkeypatch.setitem(sys.modules, "mediapipe", mp)
    return video.MediaPipePoseProvider(model), path, state


def test_video_sampling_uses_source_times_and_preserves_original_frame_indices(adapter):
    provider, path, state = adapter
    sequence = provider.extract(path)
    assert [frame.timestamp_ms for frame in sequence.frames] == [0, 67, 134]
    assert [frame.frame_index for frame in sequence.frames] == [0, 2, 4]
    assert sequence.duration_ms == 167
    assert (sequence.image_width, sequence.image_height) == (1280, 720)
    assert state.detected == [0, 67, 134]
    assert state.released and state.closed


def test_variable_frame_rate_uses_timestamps_not_assumed_fps(adapter):
    provider, path, state = adapter
    state.times = [0, 20, 80, 450, 499, 570]
    state.poses = []
    sequence = provider.extract(path)
    assert [frame.timestamp_ms for frame in sequence.frames] == [0, 80, 450, 499, 570]
    assert all(not frame.landmarks for frame in sequence.frames)
    assert sequence.duration_ms == 570


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate_time",
        "negative",
        "nan",
        "long",
        "dimensions",
        "resolution",
        "truncated",
        "rotation",
        "auto",
        "sar",
        "open",
    ],
)
def test_bad_video_fails_and_releases_decoder(adapter, failure):
    provider, path, state = adapter
    if failure == "duplicate_time":
        state.times[1] = 0
    elif failure == "negative":
        state.times[0] = -1
    elif failure == "nan":
        state.times[0] = float("nan")
    elif failure == "long":
        state.times[-1] = 120001
    elif failure == "dimensions":
        state.shapes[1] = (100, 100, 3)
    elif failure == "resolution":
        state.shapes[0] = (8000, 8000, 3)
    elif failure == "truncated":
        state.declared = 20
    elif failure == "rotation":
        state.rotation = 45
    elif failure == "auto":
        state.rotation, state.auto = 90, False
    elif failure == "sar":
        state.sar = (2, 1)
    else:
        state.opened = False
    with pytest.raises(video.VideoInputError):
        provider.extract(path)
    assert state.released


@pytest.mark.parametrize("limit", ["MAX_SAMPLED_FRAMES", "MAX_DECODED_FRAMES"])
def test_resource_limits_are_enforced(adapter, monkeypatch, limit):
    provider, path, state = adapter
    monkeypatch.setattr(video, limit, 1)
    with pytest.raises(video.VideoInputError, match="frames"):
        provider.extract(path)
    assert state.released and state.closed


def test_processing_deadline_is_checked_between_native_calls(adapter, monkeypatch):
    provider, path, state = adapter
    clock = iter([0, 181])
    monkeypatch.setattr(video, "monotonic", lambda: next(clock))
    with pytest.raises(video.VideoInputError, match="180 seconds"):
        provider.extract(path)
    assert state.released and state.closed


def test_missing_optional_dependency_has_setup_instructions(adapter, monkeypatch):
    provider, path, _state = adapter
    monkeypatch.setitem(sys.modules, "mediapipe", None)
    with pytest.raises(video.VideoInputError, match="requirements-cv.txt"):
        provider.extract(path)


def test_missing_model_is_rejected_before_loading_libraries(adapter):
    provider, path, _state = adapter
    provider.model_path = path.with_suffix(".missing")
    with pytest.raises(video.VideoInputError, match="model is missing"):
        provider.extract(path)


def test_local_cli_writes_valid_pose_and_upload_analysis_without_overwriting(tmp_path, monkeypatch):
    capture = LiveBatchRequest.model_validate(pushup_request(final=True))
    sequence = PoseSequence(capture.frames, 1280, 720, 2400)
    monkeypatch.setattr(video.MediaPipePoseProvider, "extract", lambda _self, _path: sequence)
    output = tmp_path / "result"
    args = ["fake.mp4", "--output", str(output)]
    assert analyze_video.main(args) == 0
    saved = LiveBatchRequest.model_validate_json((output / "poses.json").read_text())
    assert saved.frames == capture.frames
    result = json.loads((output / "analysis.json").read_text())
    assert result["source"]["type"] == "upload"
    assert result["summary"]["totalReps"] == 1
    assert result["exercise"]["id"] == "push-up"
    before = (output / "analysis.json").read_text()
    assert analyze_video.main(args) == 2
    assert (output / "analysis.json").read_text() == before
