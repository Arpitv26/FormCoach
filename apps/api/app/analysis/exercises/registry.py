from app.analysis.exercises.base import ExerciseProfile
from app.analysis.exercises.incline_press import INCLINE_PRESS_PROFILE
from app.analysis.exercises.lat_pulldown import LAT_PULLDOWN_PROFILE
from app.analysis.exercises.lunge import LUNGE_PROFILE
from app.analysis.exercises.pushup import PUSHUP_PROFILE
from app.analysis.exercises.squat import SQUAT_PROFILE


def planned_profile(exercise_id: str, name: str) -> ExerciseProfile:
    return ExerciseProfile(
        id=exercise_id,
        name=name,
        relevant_joints=(),
        camera_orientation="To be calibrated",
        phases=(),
        metrics=(),
        rules=(),
        coaching_cues=(),
    )


PROFILES = {
    profile.id: profile
    for profile in (
        SQUAT_PROFILE,
        PUSHUP_PROFILE,
        LAT_PULLDOWN_PROFILE,
        INCLINE_PRESS_PROFILE,
        LUNGE_PROFILE,
        planned_profile("barbell-squat", "Barbell squat"),
        planned_profile("bicep-curl", "Bicep curl"),
        planned_profile("shoulder-press", "Shoulder press"),
        planned_profile("deadlift", "Deadlift"),
    )
}
