# FormCoach dark redesign QA

final result: passed

## Observation context restored — September 27 follow-up

User approved the grouped layout but wanted the original explanation back. Each visual
finding now shows its complete observation followed by a secondary, labeled cue: Keep doing
this / Next time / Takeaway. Identical observation/cue text is not repeated. Setup is labeled
Before your reps. Layout, groups, playback and bottom diagnostics are retained across exercises.
The visual-review prompt now asks for everyday body/movement descriptions rather than gym
jargon; no assessment rules or counts changed. Existing findings remain verbatim; the new
wording instructions affect future analyses, not stored responses.

Validation: 77 frontend tests, 11 visual-review backend tests, frontend lint/build and backend
Ruff pass. Desktop and 390/320px Playwright checks pass using prior real analysis responses,
including seeking and no overflow. Inspected restored-context overview screenshots. No new
paid AI analysis was run to evaluate the prompt's writing quality.

## Review simplification — September 27

User screenshots showed repetitive observation cards, prominent diagnostics, ambiguous rep
expansion, and extra coach labels. Overview now groups concise source cues into Keep it up /
Try next set, with neutral observations only when supplied. No positive or corrective findings
are fabricated. Setup/finish labels remain explicit. Full findings, evidence timestamps,
tracking limits and partial status are retained in a collapsed About this analysis footer
outside the review workspace (upload, saved review, finalized live).

Expanded reps have a chevron, outlined/open state and inset breakdown, without repeating the
rep number or time range. Trainer heading matches the requested wording; badge and subtitle
are removed. Fixed the upload progress strip's existing 320px overflow.

Validation: 77 frontend tests pass, lint/typecheck and production build pass. Controlled
Playwright upload used the original local pulldown clip and its previously captured API
response; this was UI verification, not a fresh model analysis. Verified desktop 1440px and
390/320px layouts, overview seeking, rep expansion/seeking, coach heading, initially collapsed
footer and no horizontal overflow or page errors on both dev :3003 and rebuilt :3000.
Screenshots: `/private/tmp/formcoach-clean-production-overview-desktop.png`,
`/private/tmp/formcoach-clean-production-reps-desktop.png`,
`/private/tmp/formcoach-clean-production-coach-desktop.png`, and matching `overview-390.png`
/ `reps-320.png`. Shared DOM tests cover all four exercise IDs, neutral-only findings,
phase labels, full footer evidence, synthetic seek guards and retained chat.

## Latest palette / cinematic hero pass

Source: user palette image (sampled #0c0a0b, #464954, #f3eff5, #80af3c, #4f7c30)
and local `0d979198c2ece5a80d651d94dc62e6a0.mp4` at 1, 3 and 6 seconds.
Reference video is 1920×1080; extracted review frames are 1280×720.
Implementation: `/private/tmp/formcoach-video-hero-desktop.png` at 1440×1000,
and `/private/tmp/formcoach-video-hero-mobile.png` at 390×844, device scale 1.
Combined comparison: `/private/tmp/formcoach-hero-comparison.png`, both desktop views
normalized to 960px width while preserving their different viewport aspect ratios.
This is a typography/layout adaptation with the user's gym footage, not a car-site clone.

- Typography: single centered off-white Archivo Black headline, no gradient/shimmer/split
  slogan. Weight and rounded heavy letterforms follow the supplied title reference.
- Layout: full-width video, floating pill header, top-centered copy/action, translucent lower
  information strip. Mobile stacks the strip and preserves native page scrolling and dock.
- Tokens: exact sampled palette with neutral surface tints; old yellow chart accent replaced.
- Assets: user's existing gym clip converted to silent H.264, 1600×900, 14.76 sec / 1.22 MB.
  Poster is a real frame from that clip. No synthetic asset substitutions.
- Copy: concise FormCoach title and actual upload/live/log capabilities, without invented stats.
- Fixed a P2 11px top gap in the initial hero capture; final bounds start at y=0 on desktop.
- Browser confirms natural autoplay, looping back to ~0.4s after the end, pause/resume,
  full-offscreen pause, and OS reduced-motion pause. No page errors in the final hero pass.

No remaining P0/P1/P2 findings for this update. The earlier comparison below is historical.

## Earlier target and evidence

Scope: adapt the user's Kalo screenshot's charcoal/lime fitness-dashboard style to the
existing FormCoach product. This is a style adaptation, not a calorie-tracking clone.

Source visual truth: user attachment `Screenshot 2026-09-27 at 4.10.16 AM.png`, viewed with
the image tool from the TemporaryItems path supplied in chat. Original: 1280 × 1462 pixels.
The phone progress region (376,386)-(822,1268) was cropped and normalized to 354px width;
phone bezel and surrounding inspiration-site chrome are intentionally excluded.

Final combined comparison: `/private/tmp/formcoach-dark-comparison-final.png`.
Implementation panel: `/private/tmp/formcoach-dark-activity-comparison.png`, 354 × 855px,
390px browser width, device scale 1. A taller capture viewport permits panel inspection;
normal 390 × 844 and 360 × 900 viewport behavior was checked separately. The fixed nav
visible in the element capture is capture context, not a chart overlay fixed to the chart.

Other evidence:
- `/private/tmp/formcoach-dark-mobile-populated.png`: mobile dashboard, 390 × 844.
- `/private/tmp/formcoach-dark-populated-desktop.png`: desktop full-page populated dashboard.
- `/private/tmp/formcoach-dark-saved-desktop.png`: actual saved analysis/evidence styling.
- `/private/tmp/formcoach-dark-saved-mobile.png`: open rep measurements, mobile.
- `/private/tmp/formcoach-dark-upload-mobile-final.png`: upload selection.
- `/private/tmp/formcoach-dark-live.png`: live camera setup.

Populated history is isolated QA data made from a previously saved real analysis; it is
not installed into the user's browser. Source and implementation contain different metrics
intentionally: saved sets / logged days / detected reps replace unmeasured calories and weight.

## Comparison history and findings

1. P1: Mobile nav was positioned within the sticky header because backdrop-filter created a
   containing block. Removed that header filter; recapture confirms brand at y18 and nav
   at y759 in 390 × 844, with no overlap in the header.
2. P1: Reduced-motion preference differed at hydration. Replaced render-time preference
   with useSyncExternalStore and a stable server snapshot. Fresh reduced-motion page load
   and preference changes pass without hydration/page errors.
3. P2: Header controls overflowed in a 200% CSS-zoom stress test. Allowed the header to wrap;
   the repeated test now has no page overflow.
4. P2: Initial mobile cards were too tall for the reference's compact rhythm. Removed the
   redundant mobile side card and scroll cue, reduced hero/card/chart spacing, and made the
   date selector full-width. Final equal-content-width comparison is the combined file above.
5. P2: Four-week day targets became too narrow. Each day now has at least 44px width with
   native chart scrolling; page width stays contained.

Final comparison has no remaining actionable P0/P1/P2 issues within this adaptation scope.

## Required surfaces

- Typography: native sans, compact tracking and medium-weight titles preserve the reference's
  clear numeric hierarchy. Product headings and 14–16px body copy are deliberately larger
  than small text in the inspiration screenshot. Mobile metric notes use 12px supporting text.
- Layout: rounded charcoal cards, inset pill controls and stable mobile dock match the visual
  vocabulary. FormCoach retains upload/live actions and a taller explanation area; this is
  intentional product content, not a recreation of the reference's dense nutrition widgets.
- Color: near-black #141512, charcoal #20221e, lime #d4fa71, muted #a6aaa0; yellow marks today.
  Actions have dark text on lime; fields, errors and evidence cards were checked in dark mode.
- Assets: Lucide UI icons replace the former custom dashboard illustration. No fitness photos,
  avatars, device frames or invented graph data were needed for this product adaptation.
- Copy: actual measured/saved information, explicit unknowns and saved-video limitations.
  No fabricated calories, weight, goals, streaks or form scores.

The combined activity comparison is the focused chart/token/typography inspection. The
full-page screenshots were separately inspected for hierarchy, nav, upload and review states.

## Interaction and regression checks

76 tests, lint, typecheck, contracts and production build pass. Playwright checks at 360,
390, 1280 and 1440px have no horizontal page overflow. Period selection/day detail, review
Reps/Coach, keyboard focus, reduced-motion reload, motion pause, and actual changing animation
styles pass. Final browser checks have no page errors. Physical camera and fresh paid upload
analysis are not part of this visual change's verification.

## Follow-up polish

P3: A larger exercise-icon vocabulary could further differentiate gym cards. The current
consistent dumbbell icons work and do not block use. Source-inspired nutrition charts are
intentionally absent until actual product data exists to support them.
