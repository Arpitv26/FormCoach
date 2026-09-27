# Dashboard, upload and live UI checkpoint

**Current visual direction (later September 27):** The user replaced the light/sage direction
with a charcoal/lime fitness-dashboard reference and explicitly requested actual React Bits
and Magic UI components. See [UI_MOTION_REDESIGN.md](UI_MOTION_REDESIGN.md) for the new
components, motion controls, activity chart and Playwright validation. The earlier light
palette, Anime.js dependency and browser-access blocker below are historical.


September 27, 2026. Implementation on `backend-cv`, following the locally supplied
`UI_REDESIGN_PLAN.md` and `NEW_SESSION_PROMPT.md`. Main was not merged or modified.
The pre-existing planning edits and temporary session prompt remain outside these commits.

## Review cleanup (latest September 27)

Overview now uses grouped quick cues instead of repeated AI cards or an All observations
accordion. Detailed source observations, timestamps, limits and partial-count status live in
one collapsed About this analysis footer on upload, saved and finalized live reviews. Rep
accordions have distinct open states and no duplicate heading. Coach is titled “Chat with
your AI personal trainer”; its badge/subtitle are removed. Analysis data and backend behavior
are unchanged. See design-qa.md for the 77-test and desktop/mobile browser checks.

## Implemented

- Shared warm off-white, charcoal and sage styling, native system typography and labeled
  Dashboard / Upload / Live navigation. Mobile bottom navigation includes safe-area spacing.
- Dashboard with a real empty state, exercise shortcuts, recent sets grouped by performed
  date, exercise/source filters, saved-set counts, logged days and detected-rep totals.
  Partial tracking and unknown counts remain visible. No synthetic activity is populated.
- Central Upload workspace with exercise selection, Choose / Analyze / Review state,
  compact filming tips and an adaptive contained video player. Desktop review has two
  columns; mobile stacks the video before the results. Existing cancellation, clip/pose
  pairing, object URL cleanup, metadata limits and stale-response protection are retained.
- Overview / Reps / Coach tabs with arrow/Home/End keyboard navigation. The overview begins
  with at most two highlight groups; remaining observations are expandable. AI findings
  remain labeled separately from measured changes. Neutral/positive observations require
  no invented correction. Zero-rep movement observations remain available.
- Expandable rep rows seek the same video and retain timing, side, angle, body-line,
  torso and comparison evidence. Missing playback disables seeking. Chat stays mounted
  across tabs, resets for another set, and offers explicit retry after request failure.
- Focused live push-up setup/count/finish flow using the existing camera and counter
  controllers. Existing gym camera URLs redirect to the supported upload workspace.
- Explicit Save set after upload or successful live finalization. Date and notes are
  editable; uploads are not assumed to have happened on their analysis date. Saved
  summaries reopen at `/sets/[id]` and can be individually deleted.
- A 180 ms Anime.js heading reveal, scoped and reverted on cleanup or reduced-motion
  preference changes. Counts, video and skeleton coordinates are never animated.

## Local storage and reanalysis

`formcoach.workout-log.v1` contains a versioned envelope of saved `AnalysisResponse`
objects plus a stable local ID, analysis timestamp, performed date, notes and a nullable
analyzer revision. AJV validates results against the existing checked-in schema.
Synthetic/placeholder/unsupported results cannot become workout activity.

Repeated saves update the same entry. Reanalyzing a selected clip retains the local ID and
requires **Update saved set**; an explicit **Save as another set** can create another entry
for a new analysis. A session ID cannot appear twice. Existing records survive failed,
canceled or in-progress requests. Saved-review reanalysis requires a fresh analysis of the
reselected clip; old findings are never attached to a newly selected file.

No video, blob URL, pose track, chat or provider credential is stored. Saved review clearly
reports unavailable playback. Live has no recording. Browser storage may be cleared and
does not synchronize across devices. Quota/access errors remain visibly unsaved. Invalid
envelopes are not overwritten; unsupported individual records are skipped and retained.
Web Locks serialize updates across tabs where supported; other browsers use a synchronous
read/modify/write. Storage events refresh other open views.

## Tracker constraint

The API reports wire contract `1.0` but does **not** report the analyzer revision. Those
are different concepts. The local revision stays null, and cross-set progress trends are
withheld. After filtering to one exercise and one source, users can inspect each set’s
median counted duration, within-set range and available side-specific joint excursion.
The UI labels the version limitation and does not imply improvement from those values.
A future backend-provided revision would be needed before version-compatible trends.
Different camera views would still limit 2D comparisons.

## Verification

- 73 frontend tests pass, including DOM interaction tests for keyboard tabs, seeking,
  retained chat, new-set chat reset, zero-count observations, explicit save/update,
  quota failure, remount persistence, cross-tab deletion and missing-video saved review.
- 550 backend tests and Python schema checks pass. Backend code, analyzers, contracts,
  generated types and provider settings are unchanged. One existing Starlette warning remains.
- Frontend lint, TypeScript, generated-contract check and production build pass.
- Four previously saved real HTTP responses were rendered and storage-roundtripped:
  normal pulldown 6 (positive/neutral findings), changed pulldown 5 (adjustment), incline
  press 7 and lateral raise 7. Full analysis JSON remains identical before/after rendering
  and persistence. These are **saved-response checks**, not fresh uploads or visual QA.

Actual browser verification is blocked: `iab` is unavailable, and Chrome computer use
fails with `failed to start codex app-server: No such file or directory`. DOM tests do not
establish layout, video/overlay alignment, keyboard behavior with a mobile keyboard,
physical camera accuracy or accessibility compliance.

Before presenting: inspect 360/390 px and 1280/1440 px layouts and 200% zoom; rehearse actual
normal/changed pulldown, incline press and lateral raise uploads, skeleton toggle/seek,
replace/cancel/failure states, saved-set refresh, and a physical live start/finish/reset.
Known counting/visual-interpretation limitations in `apps/api/GYM_EXERCISES.md` remain open.

## Design references

The implementation uses original Next.js components. The public
[React Bits navigation](https://reactbits.dev/components/pill-nav) informed the compact
navigation; [Osmo’s collection](https://www.osmo.supply/collection) was a public reference
for restrained control treatments. No paid source was accessed or copied.
[Anime.js React integration](https://animejs.com/documentation/getting-started/using-with-react/)
informed scoped motion/cleanup. [Magic UI MCP](https://magicui.design/docs/mcp) was inspected,
but its MCP is not connected and was not used. No GSAP/Motion dependency was added.

Runtime additions: pinned Anime.js; existing AJV moved from dev to runtime for saved-data
validation. JSDOM and its types are dev-only for interaction tests. Run `npm ci` in `apps/web`
on another computer before starting this checkpoint.
