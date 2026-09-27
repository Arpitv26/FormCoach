"""Synthetic regressions for ordinary turns without prolonged lockout/bottom pauses."""

from math import cos, pi

import pytest

from app.analysis.exercises.pushup_segmentation import segment_pushups
from app.analysis.rep_segmentation import AngleSample


@pytest.mark.parametrize("fps", [10, 15, 30])
@pytest.mark.parametrize("offset_ms", [0, 23])
def test_twenty_continuous_cycles_with_155_degree_returns(fps, offset_ms):
    # A 1.2 s periodic motion from 155° to 85°. No special top/bottom hold.
    samples = [AngleSample(i * 100, 170) for i in range(5)]
    samples += [
        AngleSample(
            500 + offset_ms + round(i * 1000 / fps), 120 + 35 * cos(2 * pi * i / (1.2 * fps))
        )
        for i in range(round(24 * fps) + 1)
    ]
    result = segment_pushups(samples)
    assert len(result.reps) == 20
    assert all(800 <= rep.end_ms - rep.start_ms < 1500 for rep in result.reps)
    previous = ()
    for end in range(1, len(samples) + 1):
        current = segment_pushups(samples[:end]).reps
        assert current[: len(previous)] == previous
        previous = current


def test_brief_bottom_turn_is_observed_without_a_150ms_pause():
    # Two 100 ms observations below 100°, followed immediately by ascent.
    angles = [170] * 5 + [140, 125, 110, 96, 95, 112, 135, 152, 170, 170]
    result = segment_pushups([AngleSample(i * 100, angle) for i, angle in enumerate(angles)])
    assert len(result.reps) == 1
    assert result.reps[0].min_angle_deg == 96


def test_two_observed_top_samples_finish_without_extra_ascent_dwell():
    angles = [170] * 5 + [140] * 5 + [90] * 5 + [130] * 2 + [155, 156]
    samples = [AngleSample(i * 100, angle) for i, angle in enumerate(angles)]
    assert not segment_pushups(samples[:-1]).reps
    assert len(segment_pushups(samples).reps) == 1


@pytest.mark.parametrize("spike", [90, 155])
def test_isolated_zone_spike_is_not_a_completed_cycle(spike):
    angles = (
        [170] * 5 + [140] * 5 + [90] * 5 + [130] * 4 if spike == 155 else [170] * 5 + [140] * 10
    )
    angles += [spike] + ([130] * 5 if spike == 155 else [140] * 5 + [170] * 5)
    assert not segment_pushups([AngleSample(i * 100, a) for i, a in enumerate(angles)]).reps


def test_higher_frame_rate_does_not_turn_two_very_close_spikes_into_dwell():
    samples = [AngleSample(i * 100, 170) for i in range(5)]
    samples += [AngleSample(500 + i * 100, 140) for i in range(5)]
    samples += [AngleSample(1000, 90), AngleSample(1020, 90)]
    samples += [AngleSample(1040 + i * 100, 140) for i in range(5)]
    samples += [AngleSample(1540 + i * 100, 170) for i in range(5)]
    assert not segment_pushups(samples).reps


@pytest.mark.parametrize("failure", ["missing", "gap"])
def test_short_confirmation_never_bridges_tracking_loss(failure):
    angles = [170] * 5 + [140] * 5 + [90] * 5 + [130] * 5 + [155] * 5
    samples = [AngleSample(i * 100, angle) for i, angle in enumerate(angles)]
    if failure == "missing":
        samples[12] = AngleSample(1200, None)
    else:
        samples = [
            AngleSample(s.timestamp_ms + (301 if i >= 12 else 0), s.angle_deg)
            for i, s in enumerate(samples)
        ]
    assert not segment_pushups(samples).reps
