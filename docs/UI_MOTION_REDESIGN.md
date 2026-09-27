# Charcoal / lime redesign — September 27, 2026

The user's latest screenshot and explicit request supersede the earlier light/sage palette
and minimal-motion budget. Dashboard, Upload, Live, Coach and saved review now share a dark
fitness-dashboard design: near-black canvas, charcoal surfaces, lime actions and warm-yellow
current-day bars. The mobile layout is denser and retains the three-destination bottom nav.

## Actual integrated components

Adapted source lives in `apps/web/src/components/react-bits` and `magicui`:

- [React Bits SpotlightCard](https://reactbits.dev/components/spotlight-card): pointer-following
  light on dashboard/action/exercise cards; keyboard focus also reveals the treatment.
- [React Bits StarBorder](https://reactbits.dev/animations/star-border): travelling CTA edge.
- [React Bits ShinyText](https://reactbits.dev/text-animations/shiny-text): moving title sheen,
  paused outside the viewport and when decorative motion is disabled.
- [Magic UI BlurFade](https://magicui.design/docs/components/blur-fade): viewport entry reveals,
  adapted to keep text sharp rather than blurred, with visible server-rendered content.
- [Magic UI BorderBeam](https://magicui.design/docs/components/border-beam): moving perimeter
  light on the dashboard action card and empty upload panel.

`apps/web/THIRD_PARTY_NOTICES.md` preserves the upstream licenses. These are integrated,
adapted source components, not an MCP installation or a claim to use the whole libraries.
Motion is now the single JS motion engine (Anime.js removed). Lucide supplies UI icons.
Navigation also has a shared animated selection pill; the dashboard has scroll progress,
animated activity bars, and hover/press states. Native scrolling is preserved.

## Behavior

The activity chart aggregates actual saved sets by user-entered performed date over the last
7 or 28 calendar days. Day buttons reveal set and known-rep totals; 28-day charts scroll
horizontally with touch-sized targets. Empty, known zero and unknown counts remain distinct.
No sample workout history ships. Visual QA uses explicitly labeled history in an isolated
browser, built from a previously saved real analysis response.

Pause in the header disables decorative motion. OS reduced motion is honored with
hydration-safe preference handling. Live camera routes disable decorative animation so
camera/pose work remains dominant. Counts update immediately, never tweening invented values.
Weights, calories, streaks, goals, overall scores and cross-analyzer trends are not invented.
Existing upload, coach, live and saved-log controllers and all API schemas remain unchanged.

## Validation

- 76 frontend tests pass, including three new calendar aggregation regressions covering
  month/DST boundaries, period filtering, zero and unknown counts.
- Lint, typecheck, contract generation check and production build pass.
- User explicitly approved direct Playwright after the in-app/Chrome control service failed.
- Browser checks: Dashboard, Upload and Live at 360, 390, 1280 and 1440px; no page-level
  overflow. A 200% CSS-zoom stress check also passes (not a native browser zoom claim).
- Week / four-week selection, day details, saved-review Reps / Coach, motion toggle,
  OS reduced-motion hydration, and keyboard focus checked. No final page errors.
- Actual animation verified from computed styles: ShinyText background position changes,
  BorderBeam offset advances, SpotlightCard tracks pointer coordinates, and CSS animation
  becomes `none` after Pause.
- Visual checks caught and fixed a mobile fixed-nav containing-block issue, a reduced-motion
  hydration mismatch, and header overflow under CSS zoom. Mobile density was tightened.
- See root `design-qa.md` for source/implementation comparison and screenshot evidence.

This pass does not repeat paid visual analysis, physical live-camera rehearsal, or native
browser zoom. Backend code is unchanged; its prior 550-test checkpoint is not a fresh test
run in this pass. Saved responses were used for visual/interaction regression testing.

## Latest follow-up: supplied palette and video hero

The user replaced the initial lime palette with five sampled screenshot colors:
`#0c0a0b` black, `#464954` slate, `#f3eff5` off-white, `#80af3c` lime, `#4f7c30` forest.
Surfaces are neutral black/slate tints; actions use lime with black text, and white supplies
headline contrast. Forest is used for deeper green accents and chart bases.

The new title/layout reference is the supplied root video
`0d979198c2ece5a80d651d94dc62e6a0.mp4`: centered bold white text, floating navigation,
full-width background footage, compact pill action and a bottom information strip.
The former split/shimmering slogan and adjacent action card are removed from the hero.
Archivo Black is self-hosted in `public/fonts` with its SIL Open Font License.

The supplied gym scene `6389055-uhd_3840_2160_25fps (1).mp4` was converted to
`public/media/training-hero.mp4`: silent 14.76-second 1600×900 H.264 loop, 1.22 MB,
with a same-clip JPEG poster. That optimized marketing asset is deliberately tracked;
all private exercise recordings remain ignored. See the media README for provenance.

Browser verification confirms real autoplay without programmatic test forcing, loop wrap,
local pause/resume, fully-offscreen pause, and reduced-motion pause. The background is
also paused when the page is hidden. A poster remains available if playback is blocked.
Header/nav, upload and live paths remain responsive; 76 frontend regressions pass.
