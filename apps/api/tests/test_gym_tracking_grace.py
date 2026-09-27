"""Missing observations never supply dwell or completion evidence."""

import pytest

from app.analysis.exercises.incline_press import segment_incline_presses
from app.analysis.exercises.lat_pulldown import segment_lat_pulldowns
from app.analysis.rep_segmentation import AngleSample


@pytest.mark.parametrize("segment", [segment_incline_presses, segment_lat_pulldowns])
@pytest.mark.parametrize("gap,expected", [(200, 1), (201, 0), (400, 0)])
def test_grace_is_bounded_by_last_usable_observation(segment, gap, expected):
    ready = [AngleSample(i * 100, a) for i, a in enumerate([150] * 5 + [100, 90, 60, 60, 60])]
    missing = [AngleSample(1000, None)]
    end = [
        AngleSample(900 + gap + i * 100, a)
        for i, a in enumerate([110, 110, 110, 150, 150, 150, 150])
    ]
    assert len(segment(ready + missing + end).reps) == expected
    assert not segment(ready + missing).reps


@pytest.mark.parametrize("segment", [segment_incline_presses, segment_lat_pulldowns])
def test_repeated_missing_samples_do_not_extend_grace(segment):
    ready = [AngleSample(i * 100, a) for i, a in enumerate([150] * 5 + [100, 90, 60, 60, 60])]
    missing = [AngleSample(t, None) for t in range(1000, 1500, 100)]
    end = [AngleSample(1500 + i * 100, 150) for i in range(8)]
    assert not segment(ready + missing + end).reps
