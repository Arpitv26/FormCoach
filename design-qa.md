# FormCoach dark redesign QA

final result: passed

## Target and evidence

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
