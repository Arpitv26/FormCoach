# Exercise profiles and extension

The movement engine accepts FormCoach `PoseFrame` objects regardless of whether poses came
from the browser or a backend video decoder. Exercise configuration is separate from the
algorithm so a rule-based analyzer and a future lightweight ML implementation can share an interface.

## Profile representation

`apps/api/app/analysis/exercises/base.py` defines a small Python `ExerciseProfile` dataclass:

| Field | Role |
| --- | --- |
| `id`, `name` | Stable wire ID and readable name |
| `relevant_joints` | Landmarks needed by planned rules |
| `camera_orientation` | Which camera view can support the measurements |
| `phases` | Exercise state sequence |
| `metrics` | Metric keys the exercise intends to expose |
| `rules` | Named analysis rule candidates; identifiers do not implement algorithms |
| `coaching_cues` | Simple wording for future grounded rule outputs |
| `minimum_visibility` | Candidate visibility gate, default 0.7 |
| `thresholds` | Explicit candidate numerical thresholds with units in keys |
| `weights` | Intended aggregate scoring weights |
| `status` | `example` or `planned`, not a claim of working exercise support |
| `calibration_note` | Uncalibrated hackathon heuristic label |

## Squat example

`squat.py` configures standing → descent → bottom → ascent phases. It includes hips,
knees, ankles, shoulders, and foot landmarks. Candidate knee angle thresholds are 160°
for standing and 100° for bottom. **These are example engineering heuristics, not a universal
definition of a correct squat, a clinical threshold, or a finished state machine.**

The visibility threshold 0.7 is also a starting heuristic. Unknown visibility is unavailable,
not a passing value. View support must be evaluated per rule. Side-view flexion can inform
depth candidates; frontal alignment can inform knee-tracking candidates. A single uncalibrated
2D view does not automatically justify both. Return null/limitations when the view is unsuitable.

ROM, symmetry, tempo, stability, and consistency have the proposed weights documented in
SCORING.md. The fixture's scores come from authored metric inputs; profile thresholds are
not currently executed against them.

## Add an exercise after bootstrap

1. Agree on its scope, stable ID, supported view, and concrete measurable rules.
2. Add its profile under `analysis/exercises/` and register it in `registry.py`.
3. Implement its analyzer behind `MovementAnalyzer`; share geometry and visibility helpers.
4. Write small tests using known landmarks, missing landmarks, and boundary cases.
5. Test against consented clips; record why thresholds/weights were chosen.
6. Return the same `AnalysisResponse`, with measurements and reasons for unavailable fields.
7. Document supported views/limits in the backend handoff and tell the frontend which ID is ready.

No route rewrite should be necessary. If genuinely new contract fields are needed, coordinate
them using contracts/README.md before depending on them.

## Planned exercises

| ID | Bootstrap state | Eventual role |
| --- | --- | --- |
| `squat` | Example profile; no analysis | First live demo |
| `push-up` | Planned profile | Second live exercise |
| `lunge` | Planned profile | Third live exercise |
| `barbell-squat` | Registry placeholder | Possible recorded gym demo |
| `bicep-curl` | Registry placeholder | Possible recorded gym demo |
| `shoulder-press` | Registry placeholder | Possible recorded gym demo |
| `deadlift` | Registry placeholder | Possible recorded gym demo |

There is no universal exercise support. Automatic selection is a later feature; explicit
user selection is the reliable starting point.
