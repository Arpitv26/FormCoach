# Product scope

This is the post-bootstrap product roadmap. Checked items are delivered in the foundation;
unchecked items require feature work. Prioritize a reliable short demo, with prerecorded push-ups first (updated user direction).

## Must have

- [x] Frontend loads with a minimal FormCoach page.
- [x] Backend loads and health endpoint responds.
- [x] Stable contract, canonical mock, and two-team handoffs.
- [ ] Upload UI and honest processing/error states.
- [ ] Pose skeleton from a pretrained provider.
- [ ] Real-video push-up analysis and completed-rep counting (pose counter is implemented).
- [ ] Per-rep measurements/metrics and explainable summary.
- [ ] Polished responsive results experience.

## Should have

- [ ] Webcam UI and framing/permission states.

- [ ] Live feedback through the existing HTTP contract.
- [ ] Lunges.
- [ ] Evidence-grounded AI coaching.
- [ ] Worst-rep playback against matching video.
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
