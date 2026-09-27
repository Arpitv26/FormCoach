/** Frontend choices only. A route slug does not imply backend analysis support. */
export const exercises = [
  {
    slug: "push-up",
    name: "Push-ups",
    group: "live",
    backendHint: "push-up",
    equipment: "Bodyweight · floor space",
    framingTitle: "Set up a side view",
    framingText: "Place the camera beside your mat. Keep your head, shoulders, elbows, wrists, hips, and feet in view throughout the movement.",
  },
  {
    slug: "incline-dumbbell-bench-press",
    name: "Incline dumbbell bench press",
    group: "gym",
    backendHint: null,
    equipment: "Incline bench · dumbbells",
    framingTitle: "Leave room above the bench",
    framingText: "Include the bench, your upper body, and both dumbbells throughout their movement. Keep the camera clear of the equipment and walkway.",
  },
  {
    slug: "cable-lateral-raise",
    name: "Cable lateral raises",
    group: "gym",
    backendHint: null,
    equipment: "Cable station · handle",
    framingTitle: "Leave room on both sides",
    framingText: "Keep your torso and working arm visible from shoulder to hand. Leave space in the image for your arm to move without leaving the frame.",
  },
  {
    slug: "lat-pulldown",
    name: "Lat pulldowns",
    group: "gym",
    backendHint: "lat-pulldown",
    equipment: "Lat pulldown machine",
    framingTitle: "Include the overhead movement",
    framingText: "Include your seated torso, shoulders, elbows, hands, and the bar at its highest and lowest positions. Avoid placing the camera behind an obstructing machine.",
  },
] as const;

export type ExerciseOption = (typeof exercises)[number];

export function findExercise(slug: string): ExerciseOption | undefined {
  return exercises.find((exercise) => exercise.slug === slug);
}
