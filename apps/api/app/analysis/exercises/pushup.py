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
    camera_orientation="Side view; elbow and descriptive body-line angles, no form scorer.",
    phases=("top", "descent", "bottom", "ascent"),
    metrics=("rangeOfMotion", "tempo", "stability"),
    rules=("PUSHUP_REP_DURATION_CHANGED", "PUSHUP_ELBOW_EXCURSION_REDUCED"),
    coaching_cues=(),
    thresholds={
        # Counting zone, not a full-lockout/form requirement. See COUNTING.md.
        "topElbowAngleDeg": 150,
        "bottomElbowAngleDeg": 100,
        "minimumPhaseMs": 60,
        # Review thresholds, not targets or a validated definition of correct form.
        "minimumDurationChangeMs": 500,
        "durationChangeFraction": 0.30,
        "minimumExcursionReductionDeg": 15,
        "excursionReductionFraction": 0.20,
        "maximumReferenceExcursionSpreadDeg": 10,
    },
    status="example",
)
