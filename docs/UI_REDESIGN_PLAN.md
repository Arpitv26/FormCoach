# FormCoach UI overhaul

> Historical plan, retained for context. Implementation is complete for the current demo;
> later user direction superseded the light palette, Anime.js choice, hero restrictions and
> initial review-card structure below. See [UI_IMPLEMENTATION.md](UI_IMPLEMENTATION.md),
> [UI_MOTION_REDESIGN.md](UI_MOTION_REDESIGN.md) and [design-qa.md](../design-qa.md) for the
> delivered dark/green design, looping video, local workout log and grouped review.

Planning checkpoint: September 27, 2026. Based on the current implementation and the
human's upload/review screenshots. Library documentation and relevant source were reviewed;
this is not a new live-browser usability audit. No UI implementation or dependency
installation is included in this checkpoint.

## Brief

Create a calm, readable training companion that feels natural on a phone and uses desktop
space well. The demonstration remains live push-ups plus uploads for incline dumbbell
bench press, cable lateral raise and lat pulldown. A owns this frontend work.

Use warm off-white, charcoal and one muted sage family. Flat surfaces, familiar typography,
clear navigation and short useful copy. No gradients, neon, decorative display fonts,
glowing cards, animated backgrounds or endless marketing sections. Use React Bits,
Anime.js, Osmo and Magic UI selectively within one visual system.

The user has accepted the functional checkpoint for now and requested this plan. Existing
counting and visual-review limitations remain documented in GYM_EXERCISES.md and AI_COACH.md;
they do not block planning the redesign.

**Follow-up direction:** centralize all exercise uploads, give live camera its own focused
workspace, and build a workout dashboard from the user's analyzed sets. Saved session
history and data-driven trackers are now part of the plan. Start with local device storage;
accounts and cross-device synchronization are not required for this milestone.

## Problems visible in the supplied screenshots

- Video, instructions, large statistics, repeated tracking notices, chat and measurements
  occupy successive large panels. The useful takeaway is hard to find.
- The desktop review leaves substantial unused space beside a long results column.
- A finding can expose many equal-weight timestamp links at once.
- The coach and diagnostics dominate the first review, even when the user just needs to
  understand the set and watch one relevant moment.
- Current route headers differ. Home gives upload more prominence than the intended live demo.

## Visual system

| Role | Proposed treatment |
| --- | --- |
| Canvas | Warm off-white `#F7F8F5` |
| Surface | White `#FFFFFF`; use grouping and spacing before adding another card |
| Primary text | Charcoal `#20251F` |
| Secondary text | Muted dark gray-green `#5C655D`; readable labels, not pale placeholder-like copy |
| Soft accent | Sage `#DCE8D5`, with dark text |
| Primary action / focus | Deep olive `#334838`, with white action text |
| Divider | `#DDE2D9`; stronger boundaries for interactive controls when needed |
| Typography | Native system sans-serif; 16 px body, normally 14 px minimum for labels, tabular numeric measurements |
| Shape | 12–16 px panel corners; pills reserved for navigation, tabs and compact status |
| Spacing | 8 px rhythm; 16–20 px mobile gutters; 24–32 px desktop section gaps |
| Icons | One consistent thin-stroke family; labels on primary navigation |

Keep video as the main visual anchor. Use small consistent exercise illustrations or icons
for selection; avoid stock-photo galleries. Dark video framing can coexist with the light
app. Functional error/warning colors may use a muted exception with text and an icon.
Check actual text, focus and control contrast in the implemented states.

## Navigation and screen structure

Use **Dashboard / Upload / Live** everywhere. On phones, use a stable bottom bar with icon and
label and safe-area spacing. On desktop, use a compact top bar with the same destinations.
Use existing routes `/`, `/camera?exercise=push-up` and `/upload`; retain exercise links.
Coach belongs to the current set. The dashboard is the shared destination for saved upload
and live results. Keep exercise-specific upload URLs as preselected entry points into the
same upload workspace.

### Dashboard

- A short heading: “Ready for your next set?”
- Primary action: “Start live push-ups.” Secondary action: “Upload a video.”
- A compact selection of the three supported gym exercises, leading to the matching upload.
- Framing help belongs beside the relevant setup, not repeated on every exercise card.
- Keep developer/server diagnostics in a small details area; actionable connection failures
  appear beside the affected action.
- With saved sets, show a compact activity summary, recent sets grouped by date, and an
  exercise filter. Each saved set opens its review; source is labeled Upload or Live.
- Show a useful empty state with Upload and Live actions before any data exists. Do not
  populate charts, streaks or progress cards with synthetic activity.
- Keep the first dashboard small: recent activity plus one relevant trend for the selected
  exercise. Additional trackers belong in expandable detail as data becomes available.

### Upload

One central workspace supports every currently analyzed exercise. Changing the exercise
updates framing help and analysis selection within that workspace. Home exercise shortcuts
arrive here with the selection filled in; avoid separate upload tools for each exercise.

Represent the flow as **Choose → Analyze → Review**, without adding extra Next buttons.
Exercise selection and file selection share one screen. After selection, show the preview,
filename, Replace action and one prominent Analyze button.

Move the large right-hand filming guide into “Filming tips.” Keep file limits as one quiet
line. Show actual request states with a simple pending indicator; the backend does not
currently expose a percentage or precise processing phases. Retain cancel/error/retry behavior.

### Review — the first screen to design in detail

Desktop: use a two-column workspace, with video on the left and the current review section
on the right. Keep the video available while exploring evidence. Adapt the column balance
to portrait and landscape clips; contain the full frame without cropping tracked joints.
Keep the player within the available viewport height instead of stretching portrait footage
into an oversized landscape box.

Phone: video first, a compact summary row, then **Overview / Reps / Coach** tabs. Keep one
main page scroll and a reachable composer. The keyboard, bottom navigation and safe areas
must not cover Send or the last message.

The summary is a compact “6 detected reps · 22 s” style row using the actual result. When
tracking is partial, keep one concise visible notice (“Some movement may be uncounted”)
with expandable reasons. Do not infer correctness from the count or hide a material limitation.

**Overview:** show up to two useful highlights initially, with one short observation and
one cue where supplied by evidence. A positive or neutral finding is a valid complete
overview; never fill a correction slot with an invented fault. Keep the existing distinction
between measured movement and AI visual observations visible through short labels.
Each highlight gets one “Watch moment” action; additional cited times sit in details.
“All observations” exposes the remaining findings, including setup/finish context.

**Reps:** compact selectable rows with rep number, time and one useful measurement. Selecting
a row seeks the existing player and opens that rep's details. Keep units, side, unknowns and
timing meaning available. Optional comparison chart belongs here. Empty or unsupported
comparison sections should not occupy the overview.

**Coach:** a clean conversation with two relevant starter prompts, a clear composer and
evidence behind a disclosure. Keep paragraphs readable and allow lists for requested
rep-by-rep answers. Longer replies remain accessible; do not silently cut their meaning.
Keep history scoped to this set and show an understandable retry/fallback state.

Zero completed reps can still have useful movement observations. Show those in Overview;
do not replace them with an empty chart or “nothing happened.” Unknown scores stay absent.

### Live

Make the camera the dominant area. Before starting: a short setup cue, camera controls and
Start set. During the set: a large actual rep count, concise tracking state and one clear
Finish set action. Keep framing instructions out of the active view unless needed.
After finishing, reuse the review structure with the evidence available for live analysis.
Do not imply that live sets received the uploaded-image visual review.

### Saved sets and trackers

Both entry points follow **Analyze → Review → Save set → Dashboard**. Saving is an explicit,
lightweight action, with a saved state that prevents double-counting. Failed requests and
in-progress live batches never become completed saved sets. A zero-rep analysis can still
be saved with its movement observations. Reanalysis updates the chosen saved set or requires
an explicit “Save as another set”; it must not silently duplicate workout activity.

| Tracker | Data and presentation |
| --- | --- |
| Activity | Dates with saved sets, set count and exercise breakdown; call dates “logged days,” not verified attendance |
| Detected reps | Per-set values and totals, with partial/unknown counts visibly distinguished; unknown is not zero |
| Rep timing | Per-set median and within-set variation from measured rep durations; preserve exercise-specific timing meaning |
| Measured movement | Available joint-angle/excursion trends for a selected exercise and side, with measurement details |
| Review notes | Reopen actual positive/neutral/adjustment findings with their evidence; do not turn AI prose into a numerical score |

Treat these as descriptive trackers. A longer rep, larger angle or higher rep count does not
automatically mean better form. Show a trend only with at least two comparable sets; split
live and upload sources by default and explain that a changed camera view can change 2D
angles. Do not mix different exercise measurements or analysis versions into an unlabeled
trend. Clip length is not workout duration, and summed rep time is not total training time.
Weights, calories, strength gains and overall form scores are not currently measured.

First storage milestone: a small versioned browser-local store for saved analysis results,
exercise, source, analysis time, user-editable performed date and optional notes. Upload
analysis time is not proof of when the workout happened. Label the log “Saved on this device”
and support deleting individual sets. Handle unavailable/full storage with a clear unsaved
state. No database, login or cloud service is needed for this first version.

Do not persist raw pose tracks or video files by default. A saved summary can reopen after
refresh, but playback and skeleton seeking require the original clip/track to be available
again. Show that state honestly and offer to reselect/reanalyze the clip; never render stale
object URLs or present a different clip as the evidence. Local storage can be cleared by the
browser; cross-device history can be a separate future milestone if requested.

## Component and motion shortlist

These are candidates and adaptation decisions, not a commitment to install every library.

| Reference | Intended use | Adaptation |
| --- | --- | --- |
| [React Bits Pill Nav](https://reactbits.dev/components/pill-nav) | Shared desktop navigation and selected-state treatment | Next.js links, simpler transitions, accessible current-page state; mobile uses three visible destinations |
| [React Bits Stepper](https://reactbits.dev/components/stepper) | Compact upload stage indicator | Reflect actual flow; remove unnecessary form wizard controls |
| [React Bits Animated List](https://reactbits.dev/components/animated-list) | Selectable rep rows | Disable gradients, avoid nested mobile scrolling, retain native button/keyboard semantics |
| [Anime.js React integration](https://animejs.com/documentation/getting-started/using-with-react/) | Main motion engine: tab/selection transitions, result entry, disclosure movement | Component-scoped effects with cleanup; no camera/pose animation |
| [Osmo collection](https://www.osmo.supply/collection) | Button press/hover polish and accordion timing | Use public patterns or legitimately available source; adapt to React and the shared palette |
| [Magic UI Blur Fade](https://magicui.design/docs/components/blur-fade) | Candidate for a single result-entry reveal | No text blur; short duration; use only if it adds value beyond the Anime.js implementation |

The inspected React Bits Pill Nav source imports GSAP and react-router-dom; other shortlisted
React Bits components use Motion. The existing app has no animation dependency. Review the
specific source and license before integrating; adapt the useful patterns to Next.js and
prefer one animation engine. Preserve required attribution. Avoid adding several engines
for effects that Anime.js or CSS already handles.

[Magic UI's official MCP](https://magicui.design/docs/mcp) is documented but is not connected
to this Codex session. Check its supported configuration during implementation and use it
if available. Official docs/source remain usable; do not claim the MCP was used or install
an unrelated editor's configuration. Osmo paid resources are not assumed to be accessible.

Motion budget: roughly 150–240 ms for ordinary transitions, small displacement, no long
stagger delaying access to results. Keep text sharp. Respect reduced motion using scoped
media conditions or CSS. Update confirmed counts immediately; do not tween through invented
rep values. Never run decorative loops alongside MediaPipe, animate the skeleton's source
coordinates, hide information behind hover, or hijack scrolling.

## Implementation sequence

1. **Visual target:** make the upload review screen at phone and desktop sizes using real
   representative content. Include a positive/neutral set and a set with an adjustment.
   Settle hierarchy, spacing, player size, navigation and type before expanding all routes.
2. **Foundation:** implement tokens, shared navigation, buttons, tabs, disclosures and the
   Dashboard empty state.
   Keep this as a small verified commit.
3. **Upload and review:** implement the compact selection flow, adaptive player layout,
   Overview/Reps/Coach, meaningful empty/error states and timestamp navigation.
4. **Live and conversation:** carry the same system into setup, active count, finished set
   and longer coach conversations; verify mobile keyboard behavior.
5. **Saved sets and trackers:** connect both analysis paths to the local log, saved review,
   exercise filters and the bounded trackers above. Test persistence, duplicate prevention,
   deletion, partial/unknown data and missing-video states before displaying trends.
6. **Motion and rehearsal:** add selected effects, inspect browser screenshots at phone and
   desktop sizes, run existing checks, and rehearse the three uploads plus live push-ups.

Implementation touch points: `apps/web/src/app/{layout.tsx,page.tsx,globals.css}`, upload and
camera route pages, `video-upload`, `uploaded-results`, `session-results`, `coach-panel`,
`rep-overview`, `movement-observations`, `webcam-setup` and their styles.

Reuse the current upload, live, coach and pose controllers. Preserve cancellation, stale
response rejection, result/clip pairing, camera cleanup, skeleton synchronization and
session-bound history. The dashboard needs new frontend persistence and aggregation logic;
use existing analysis data without changing analyzer rules or the API contract. Version the
local saved-set format separately and keep unsupported/older records from breaking the log.
Before editing, recheck Git status and B's latest published work for overlap, and read the
local Next.js guides required by apps/web/AGENTS.md.

## Completion checks

- Review first view makes the selected exercise, detected count, useful takeaway and next
  action clear. Extra diagnostics require deliberate expansion.
- Phone checks at 360/390 px and desktop checks at 1280/1440 px; no horizontal overflow,
  cropped joints, covered controls or unreadably small supporting text. Check 200% zoom.
- Keyboard navigation, visible focus, tab semantics, labeled controls, reduced motion and
  44 px minimum primary touch targets. Essential actions work without hover.
- Actual uploads: normal/changed pulldown, incline press and lateral raise; verify findings
  stay paired with the selected clip and timestamp buttons seek correctly.
- Switching/replacing clips, canceled uploads, backend failure, AI unavailable, missing
  visual review, unknown count and zero-rep movement observations remain understandable.
- Live start/finish/reset, count updates, camera release and skeleton playback keep working.
- Saved upload and live sets survive refresh on the same browser, appear once in the log,
  can be deleted, and retain their actual findings. Saving failures are visible.
- Tracker totals distinguish partial/unknown counts. Exercise/source filters isolate
  comparable measurements; an empty or single-set history does not imply a progress trend.
- Saved summaries with no available video remain readable, with playback clearly unavailable.
- Run frontend tests, lint, typecheck, contracts check and production build. Add behavior
  tests for changed interactions; do not create tests that merely mirror CSS class names.
- Compare backend data before/after styling for the same saved response. Keep numerical
  results and meaning intact. Record actual browser checks; screenshots in this plan are
  not evidence that the future implementation works.
