from app.analysis.exercises.base import ExerciseProfile

SQUAT_PROFILE = ExerciseProfile(
    id="squat",
    name="Squat",
    relevant_joints=(
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
        "left_foot_index",
        "right_foot_index",
    ),
    camera_orientation="Side view for knee flexion; front view for tracking/symmetry.",
    phases=("standing", "descent", "bottom", "ascent"),
    metrics=("rangeOfMotion", "symmetry", "tempo", "stability", "consistency"),
    rules=("depth_candidate", "knee_tracking_candidate", "tempo_variation_candidate"),
    coaching_cues=("Use a controlled pace.", "Keep your knee tracking over your toes."),
    thresholds={"standingKneeAngleDeg": 160, "bottomKneeAngleDeg": 100},
    weights={
        "rangeOfMotion": 0.30,
        "symmetry": 0.20,
        "tempo": 0.15,
        "stability": 0.20,
        "consistency": 0.15,
    },
    status="example",
)
