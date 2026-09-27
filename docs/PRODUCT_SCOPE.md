# Product scope

This is the post-bootstrap product roadmap. Checked items are implemented;
unchecked items require feature work. Prioritize a reliable short demo, with prerecorded push-ups first (updated user direction).
See NEXT_STEPS.md for current ownership and the order of work. B finishes frontend features;
A then takes over the visual overhaul after integration.

## Must have

- [x] Frontend loads with a minimal FormCoach page.
- [x] Backend loads and health endpoint responds.
- [x] Stable contract, canonical mock, and two-team handoffs.
- [x] Upload UI and honest processing/error states.
- [x] Live and uploaded-video pose skeleton from a pretrained provider (physical webcam demo check pending).
- [x] Real-video push-up analysis and completed-rep counting (four clips match human counts).
- [x] Per-rep descriptive elbow/timing measurements and explainable summary (quality scores are separate).
- [ ] Polished responsive results experience.

## Should have

- [x] Webcam UI and framing/permission states.

- [ ] Live feedback through the existing HTTP contract.
- [ ] Lunges.
- [x] Evidence-grounded backend coaching, with optional OpenAI selection.
- [ ] Coach panel/interactions (B in progress).
- [x] Rep-start/minimum-angle playback against the matching video.
- [ ] Real positive comparison flag validated against footage.
- [ ] Body-alignment measurement and evidence-supported review cue.
- [ ] Justified form scoring and worst-form rep ranking; unavailable until measurements/rubric are validated.
- [ ] Clear per-rep and set-level graphs.

## Wow / stretch

- [ ] Automatic exercise recognition from landmark sequences.
- [ ] Reference/ghost motion overlay.
- [ ] Measured form degradation trends (avoid claiming diagnosed fatigue).
- [ ] Barbell path.
- [ ] Lightweight custom classifier.
- [ ] Workout history and form fingerprint.
- [ ] Voice feedback.

Other gym exercises are deferred until the push-up video demo is reliable. They are
planned profiles, not a promise of supported analysis. Prefer one convincing exercise over
20 unreliable ones. Training a pose model, authentication, billing, databases, and complex
infrastructure are outside the initial demo scope.

Any stretch task waits until the recorded push-up path, matching measured results, and pitch rehearsal work.
