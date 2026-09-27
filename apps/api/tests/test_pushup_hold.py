from app.analysis.exercises.pushup_segmentation import segment_pushups
from app.analysis.rep_segmentation import AngleSample


def test_five_pushups_with_seven_second_bottom_hold_in_fourth_rep():
    # Synthetic continuous observations: a long bottom pause is still one full cycle.
    top = [170] * 6
    normal = [140] * 5 + [80] * 5 + [130] * 5 + top
    held = [140] * 5 + [80] * 70 + [130] * 5 + top
    angles = top + normal * 3 + held + normal
    result = segment_pushups([AngleSample(i * 100, angle) for i, angle in enumerate(angles)])
    assert len(result.reps) == 5
    assert result.reps[3].end_ms - result.reps[3].start_ms > 7000
    assert result.tracking_breaks == 0
