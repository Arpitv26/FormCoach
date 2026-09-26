from app.analysis.exercises.base import ExerciseProfile

LUNGE_PROFILE = ExerciseProfile(
    id="lunge",
    name="Lunge",
    relevant_joints=(
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    ),
    camera_orientation="Side view for flexion; front view for symmetry.",
    phases=("standing", "descent", "bottom", "ascent"),
    metrics=("rangeOfMotion", "symmetry", "tempo"),
    rules=(),
    coaching_cues=(),
)
