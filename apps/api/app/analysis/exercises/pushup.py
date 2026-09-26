from app.analysis.exercises.base import ExerciseProfile

PUSHUP_PROFILE = ExerciseProfile(
    id="push-up",
    name="Push-up",
    relevant_joints=(
        "left_shoulder",
        "left_elbow",
        "left_wrist",
        "left_hip",
        "left_ankle",
        "right_shoulder",
        "right_elbow",
        "right_wrist",
        "right_hip",
        "right_ankle",
    ),
    camera_orientation="Side view; elbow flexion only until body-line metrics are validated.",
    phases=("top", "descent", "bottom", "ascent"),
    metrics=("rangeOfMotion", "tempo", "stability"),
    rules=(),
    coaching_cues=(),
    thresholds={"topElbowAngleDeg": 160, "bottomElbowAngleDeg": 100},
    status="example",
)
