# Frontend demo rehearsal

Keep prerecorded push-ups as the primary presentation. These are manual acceptance checks,
not a claim that all physical-camera/browser combinations were tested automatically.
Run the frontend on localhost or HTTPS. Use the configured API; keep provider keys backend-only.

## Uploaded clip

- [ ] Analyze one consented landscape clip and one portrait clip. Compare the count with a human.
- [ ] Play inline, toggle the skeleton, seek to a rep start and minimum-angle moment. Verify alignment.
- [ ] Switch counted-time/elbow-range charts. Confirm units and unknown values are correct.
- [ ] Review any actual comparison flags against matching video. No flags does not mean perfect form.
- [ ] If no real clip produces a flag, label the synthetic comparison walkthrough explicitly.
- [ ] Replace/remove a clip during upload and coaching; old results/answers must not return.
- [ ] Try an invalid file, unsupported codec and unavailable backend. Confirm actionable errors.

## Coach

- [ ] Request a local summary and next-set guidance; see a short reply and expand its measurements/limitations.
- [ ] Ask about a measured rep with optional OpenAI enabled on the backend. Verify the wording against its evidence, then ask a follow-up about the same rep.
- [ ] Local free-form QA explains AI is unavailable. Missed-count troubleshooting still works locally.
- [ ] Tell the coach a count was missed, then mention a hold. It must not invent why it happened.
- [ ] Check partial and insufficient-data results; missing scores must stay unavailable.
- [ ] Cancel an explanation and request again; there should be no automatic retry or duplicate request.

## Physical laptop webcam

- [ ] Enable camera; wait for the model, then start a side-view push-up set with a brief top pause.
- [ ] Compare completed cycles with a human count. This validates the demo set, not general accuracy.
- [ ] Leave/re-enter the frame briefly. Tracking gaps must not become fabricated continuous motion.
- [ ] Finish, inspect final results, then start a new set. Previous counts must not carry over.
- [ ] Finish set; camera tracks are released. Start a new set without carrying over counts/history.
- [ ] Perform five reps, including a comfortable bottom pause if desired. Compare with a human.
- [ ] Open “Count look wrong?” and download troubleshooting data before starting another set.
      Save privately under ignored artifacts and replay the exact capture; do not commit it.
- [ ] Hide the page during capture; the set ends. Returning does not silently resume it.
- [ ] Change exercise or navigate away during a request; camera and obsolete requests stop.
- [ ] Stop the backend mid-set; capture pauses and manual retry finalizes the frozen observations.
- [ ] Test missing/slow model and permission denial. A preview alone must not enable tracking claims.

## Presentation and accessibility

- [ ] Rehearse at desktop and phone widths, with keyboard-only controls and visible focus.
- [ ] Explain that the pose model is pretrained, while the team built rep analysis and evidence review.
- [ ] Do not claim form scores, injury prediction, fatigue detection, or supported gym analyzers.
- [ ] Keep a working consented backup clip locally. Never commit personal recordings or pose captures.

Automated checks: `npm run contracts:check`, `npm run lint`, `npm run typecheck`, `npm test`,
`npm run build` from `apps/web`. Browser smoke checks can use simulated media and controlled
API responses; those do not replace the physical-camera and actual-backend checks above.
