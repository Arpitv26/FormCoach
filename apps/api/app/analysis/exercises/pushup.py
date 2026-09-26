from app.analysis.exercises.base import ExerciseProfile

PUSHUP_PROFILE = ExerciseProfile(
    id="push-up",
    name="Push-up",
    relevant_joints=("left_shoulder", "left_elbow", "left_wrist", "left_hip", "left_ankle"),
    camera_orientation="Side view; calibrate before implementation.",
    phases=("top", "descent", "bottom", "ascent"),
    metrics=("rangeOfMotion", "tempo", "stability"),
    rules=(),
    coaching_cues=(),
)
