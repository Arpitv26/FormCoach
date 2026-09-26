from dataclasses import replace
from math import cos, radians, sin

import pytest

from app.analysis.exercises.squat_segmentation import SquatSegmentationConfig, segment_squats
from app.analysis.geometry import measure_joint_angle
from app.analysis.rep_segmentation import AngleSample
from app.domain.pose import LANDMARK_NAMES, PoseFrame, PoseLandmark

STANDING = [170] * 5
CYCLE = [140] * 5 + [90] * 5 + [130] * 5 + STANDING


def samples(angles, interval=100):
    return [AngleSample(index * interval, angle) for index, angle in enumerate(angles)]


def test_completed_squat_has_observed_boundaries_and_all_phases():
    sequence = samples(STANDING + CYCLE)
    result = segment_squats(sequence)
    assert len(result.reps) == 1
    rep = result.reps[0]
    assert (rep.start_ms, rep.bottom_ms, rep.end_ms) == (600, 1100, 2300)
    assert rep.min_angle_deg == 90
    assert result.current_phase == "standing"
    phases = [segment_squats(sequence[:end]).current_phase for end in (5, 10, 15, 20, 25)]
    assert phases == ["standing", "descent", "bottom", "ascent", "standing"]


def test_multiple_reps_and_extra_standing_do_not_double_count():
    result = segment_squats(samples(STANDING + CYCLE * 3 + STANDING * 3))
    assert len(result.reps) == 3
    for previous, current in zip(result.reps, result.reps[1:], strict=False):
        assert previous.end_ms < current.start_ms


@pytest.mark.parametrize("cutoff", [0, 2, 5, 10, 15, 20, 23])
def test_unfinished_reps_are_never_counted(cutoff):
    assert segment_squats(samples(STANDING + CYCLE)[:cutoff]).reps == ()


def test_starting_at_bottom_requires_standing_before_a_complete_rep():
    beginning = [90] * 5 + [130] * 5 + STANDING
    assert segment_squats(samples(beginning)).reps == ()
    assert len(segment_squats(samples(beginning + CYCLE)).reps) == 1


def test_shallow_attempt_is_discarded_and_next_complete_rep_is_counted():
    shallow = [140] * 5 + [120] * 5 + STANDING
    assert segment_squats(samples(STANDING + shallow)).reps == ()
    assert len(segment_squats(samples(STANDING + shallow + CYCLE)).reps) == 1


def test_standing_jitter_and_single_frame_spikes_do_not_count():
    angles = STANDING + [149, 151] * 10 + STANDING + [90] + STANDING
    result = segment_squats(samples(angles))
    assert result.reps == ()
    assert result.current_phase == "standing"


def test_spike_during_descent_does_not_fake_bottom():
    result = segment_squats(samples(STANDING + [140] * 5 + [90] + [140] * 5 + STANDING))
    assert result.reps == ()


def test_bottom_bounce_is_one_rep():
    bounce = [90] * 5 + [130] * 5
    result = segment_squats(samples(STANDING + CYCLE[:-5] + bounce + STANDING))
    assert len(result.reps) == 1


@pytest.mark.parametrize("missing_index", [8, 13, 18, 22])
def test_tracking_loss_discards_unfinished_rep_and_can_recover(missing_index):
    angles = STANDING + CYCLE
    angles[missing_index] = None
    first = segment_squats(samples(angles))
    assert first.reps == ()
    result = segment_squats(samples(angles + STANDING + CYCLE))
    assert len(result.reps) == 1
    assert result.tracking_breaks == 1
    assert result.reps[0].start_ms >= len(angles) * 100


def test_completed_rep_survives_loss_and_trailing_unknown_is_reported():
    result = segment_squats(samples(STANDING + CYCLE + [None] * 5))
    assert len(result.reps) == 1
    assert result.current_phase == "unknown"
    assert result.last_smoothed_angle_deg is None
    assert result.tracking_breaks == 1


@pytest.mark.parametrize(("extra_gap", "expected_reps"), [(200, 1), (201, 0)])
def test_elapsed_time_gap_boundary(extra_gap, expected_reps):
    sequence = samples(STANDING + CYCLE)
    sequence = [
        replace(sample, timestamp_ms=sample.timestamp_ms + extra_gap) if index >= 13 else sample
        for index, sample in enumerate(sequence)
    ]
    result = segment_squats(sequence)
    assert len(result.reps) == expected_reps
    assert result.tracking_breaks == (0 if expected_reps else 1)


def test_gap_during_smoothing_warmup_clears_old_samples():
    result = segment_squats([AngleSample(0, 170), AngleSample(1000, 170), AngleSample(1100, 170)])
    assert result.current_phase == "unknown"
    assert result.last_smoothed_angle_deg is None
    assert result.tracking_breaks == 1


def test_too_fast_cycle_does_not_count():
    config = SquatSegmentationConfig(minimum_phase_ms=20, smoothing_window=1)
    sequence = samples(STANDING + CYCLE, interval=20)
    assert segment_squats(sequence, config=config).reps == ()
    # The same transitions can count if an explicitly different duration policy permits them.
    assert len(segment_squats(sequence, config=replace(config, minimum_rep_ms=200)).reps) == 1


def test_stale_attempt_times_out_and_next_rep_recovers():
    angles = STANDING + [140] * 5 + [90] * 160 + [130] * 5 + STANDING
    assert segment_squats(samples(angles)).reps == ()
    assert len(segment_squats(samples(angles + CYCLE)).reps) == 1


def test_cumulative_replay_is_deterministic_and_does_not_mutate_input():
    sequence = samples(STANDING + CYCLE * 2)
    before = list(sequence)
    first = segment_squats(sequence[:25])
    result = segment_squats(sequence)
    assert result == segment_squats(sequence)
    assert result.reps[:1] == first.reps
    assert len(first.reps) == 1 and len(result.reps) == 2
    assert sequence == before
    assert segment_squats([]).reps == ()


@pytest.mark.parametrize("timestamps", [(0, 0), (100, 0)])
def test_duplicate_or_reversed_timestamps_are_rejected(timestamps):
    with pytest.raises(ValueError, match="strictly increase"):
        segment_squats([AngleSample(timestamp, 170) for timestamp in timestamps])


@pytest.mark.parametrize("angle", [-1, 181, float("nan"), float("inf")])
def test_bad_angle_is_not_silently_treated_as_a_rep(angle):
    with pytest.raises(ValueError, match="Angles"):
        AngleSample(0, angle)


@pytest.mark.parametrize("timestamp", [-1, 1.5, True])
def test_bad_sample_time_is_rejected(timestamp):
    with pytest.raises(ValueError, match="timestamps"):
        AngleSample(timestamp, 170)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"hysteresis_deg": 0},
        {"bottom_angle_deg": 160},
        {"standing_angle_deg": float("nan")},
        {"minimum_phase_ms": 0},
        {"maximum_gap_ms": -1},
        {"smoothing_window": 2},
        {"smoothing_window": 0},
        {"maximum_rep_ms": 800},
    ],
)
def test_invalid_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        SquatSegmentationConfig(**kwargs)


def test_pose_measurements_feed_counter_and_visibility_loss_is_preserved():
    # Synthetic image geometry with known angles, not a recorded human squat.
    measured = []
    for index, angle in enumerate(STANDING + CYCLE):
        points = [
            (500, 200),
            (500, 400),
            (500 + 200 * sin(radians(angle)), 400 - 200 * cos(radians(angle))),
        ]
        names = ("left_hip", "left_knee", "left_ankle")
        frame = PoseFrame(
            frame_index=index,
            timestamp_ms=index * 100,
            landmarks=[
                PoseLandmark(
                    index=LANDMARK_NAMES.index(name),
                    name=name,
                    x=x / 1280,
                    y=y / 720,
                    visibility=0.9,
                )
                for name, (x, y) in zip(names, points, strict=True)
            ],
        )
        angle_result = measure_joint_angle(
            frame, names, image_width=1280, image_height=720, minimum_visibility=0.7
        )
        measured.append(AngleSample(frame.timestamp_ms, angle_result.angle_deg))
        if index == 13:
            frame.landmarks[1].visibility = None
            unavailable = measure_joint_angle(
                frame, names, image_width=1280, image_height=720, minimum_visibility=0.7
            )
            lost_sample = AngleSample(frame.timestamp_ms, unavailable.angle_deg)
    assert len(segment_squats(measured).reps) == 1
    measured[13] = lost_sample
    assert segment_squats(measured).reps == ()
