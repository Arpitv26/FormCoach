# IMG_6942: four-rep timing variation review

Reviewed 2026-09-26 on backend code `5dfaa63` (runtime unchanged since `4b87e35`).
Human annotation: **four completed push-ups; first two normal, third slower, fourth faster**.
The original MOV stays private and ignored at the repository root.

## Result

The file decodes without conversion: 84.97 MiB, 3840 × 2160, approximately 59.97 fps,
799 source frames, about 13.3 seconds. Fresh MediaPipe Full extraction produced 200 pose
samples. The left elbow and left shoulder/hip/ankle passed the existing visibility checks
in all 200 samples. Analysis is `complete`, with **4 counted reps**, zero issues and null scores.

| Rep | Start–end | Counted duration | Minimum-angle moment | Observed elbow excursion |
| --- | --- | --- | --- | --- |
| 1 | 3.935–5.670 s | 1.735 s | 4.735 s | 95.980° |
| 2 | 6.537–7.937 s | 1.400 s | 7.137 s | 96.011° |
| 3 | 8.737–11.805 s | 3.068 s | 10.538 s | 104.005° |
| 4 | 12.005–13.073 s | 1.068 s | 12.405 s | 100.735° |

A half-second frame sequence visibly shows four cycles and the longer third cycle.
Twelve additional actual frames at the reported start/minimum/end moments were inspected
with same-frame shoulder/elbow/wrist and shoulder/hip/ankle overlays. Landmarks plausibly
align with the participant; decoded frame timestamps are within 35 ms of pose timestamps.
This is sampled visual review, not manually annotated millisecond ground truth or browser seek verification.
Counting windows include smoothing/confirmation delay and are not isolated lifting/lowering times.

## Expected timing flag was missed

The unchanged timing rule requires two preceding durations to differ by at most 20% of their
median before it compares the next rep. For rep 3:

- References: 1735 and 1400 ms; median 1567.5 ms.
- Spread: `335 / 1567.5 × 100 = 21.3716%`, above the 20% eligibility limit.
- Rep 3 is 3068 ms, but the duration comparison is omitted before the change threshold
  is evaluated. The absence of a flag does not mean unchanged pace.
- Rep 4 references reps 2/3 (1400/3068 ms), whose spread is 74.6643%; it is also ineligible.
  The current rolling-reference policy does not compare it to the first two reps instead.

Both excursion comparisons are eligible. Their deltas are +8.009° (rep 3) and +0.727°
(rep 4), so neither triggers the separate reduction rule. This clip supplies no positive
excursion-reduction validation.

The observed timing pattern agrees with the human description. **Counting passed; the intended
positive timing-detection checkpoint failed.** No thresholds, timestamps or pose values were
changed to produce a flag. This is useful evidence about reference eligibility, not an extraction bug.

## API and coach checks

Cumulative replay through TestClient live-route handling, with four expected reps and an
expected timing flag on rep 3, returns `comparison_mismatch`: missing timing flag `[3]`, no
unexpected timing flags, and matching zero range flags. Completed reps remain stable, the
repeated final response is identical, and upload-tool/replay reps and timeline match exactly.

Local `next_set` coaching returns HTTP 200 with resolvable evidence paths and no invented
flag/score. It currently selects the count, rep 1 duration and rep 1 body-line angle; it does
**not** surface the observed slower third rep when the timing comparison is ineligible.
No paid OpenAI call was made. A fresh multipart upload/browser pass for this clip is still pending.

Private artifacts:

- `artifacts/review-6942/`: original extracted poses, analysis, replay and local coach result.
- `artifacts/review-6942-visual/`: sequence and twelve annotated rep-moment frames.

## Next backend checkpoint

Explain why a per-rep comparison is unavailable, and review the timing-reference policy
using this failure case and the original four clips. Keep descriptive durations available
even when an automatic flag is withheld. Consider sampling/segmentation uncertainty and
reference variation explicitly before changing any eligibility rule. A proposed change needs
synthetic boundary/gap tests, regressions on all five clips and separate validation footage;
after using 6942 to develop a change, do not claim it is independent validation of that change.
Coordinate any additional measurement keys with the frontend handoff. Keep scores null.

Do not request a replacement recording merely to satisfy the current threshold. The uploaded
clip already provides the intended pace variation and remains a useful review case.
