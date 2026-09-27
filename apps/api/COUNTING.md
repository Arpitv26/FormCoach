# Push-up counting correction — September 26, 2026

## Reproduced failures

The human reported about 5–6 reps in a live capture (4 returned), then 20 in a later live
set (9 returned) and 5 when uploading its recording, `IMG_6943.MOV`.

- The supplied live JSON reproduces **4**. Around 8.47–9.44 s, an additional bend/return
  was discarded: the smoothed angle was below 100° for 100 ms, less than the old 150 ms
  bottom requirement. Eight unusable samples occur after the set, not in that missed cycle.
  The human's exact count for this JSON is uncertain; there is no matching video.
- Fresh native extraction of IMG_6943 reproduces **5**: 464 samples, upright 2160×3840,
  **zero unavailable selected-elbow samples and zero tracking breaks**. Successive cycles
  were merged into intervals lasting 11.94 s and 10.00 s. Several top returns peak around
  154.5–159°, below the old 160° requirement; other returns are too brief for its dwell.
- The separate live JSON that returned 9 was not supplied. Its exact failure cannot be
  reconstructed from the upload: browser and upload models/sample times differ.

This points to unsuitable counting rules. No retraining, new model, interpolation or
OpenAI call is involved in the correction.

## Policy v2 — push-ups only

| Rule | Value / meaning |
| --- | --- |
| Top/return zone | Elbow angle >=150° |
| Bend zone | Elbow angle <=100° |
| Hysteresis | 10°; descent <=140°, ascent >=110° |
| Confirmation | Consecutive raw observations over >=60 ms, with the current three-sample median also meeting the threshold |
| Overlapping evidence | Collect zone clocks together; confirming ascent cannot restart already-observed top evidence, nor descent restart bottom evidence |
| Rep duration | 800–15000 ms, unchanged |
| Tracking loss | Any unavailable selected angle or timestamp gap >300 ms discards the unfinished cycle, unchanged |
| Side | First usable anatomical side remains locked, unchanged |

The 150° return zone tolerates visibly extended returns whose 2D estimates fall below 160°.
It is a counting heuristic, **not a full-lockout standard or quality grade**. At 10/15 fps,
60 ms requires at least two observations; higher rates require more. Median confirmation
rejects an isolated spike. Sustained bad estimates can still mislead the counter. These
values were revised using development footage and need independent validation.

Readiness, a confirmed bend and return remain required. A long bottom hold stays one rep.
Starting at the bottom, unfinished/shallow/too-fast cycles and tracking gaps may remain
uncounted. Uncounted movement does not mean bad form. Legacy squat behavior is unchanged.

## Timing and compatibility

Contract remains **1.0**: no schema, type, endpoint or frontend algorithm changes.
Start is the first raw descent-zone observation in the confirmed run. Extrema still begin
at descent confirmation; end confirms return; the minimum is the first lowest smoothed
angle within that window. Many boundaries occur earlier, so durations, measurement windows,
body-line sample counts and comparisons change. Do not assert old timestamps are unchanged.
The synthetic fixtures retain their authored original intervals. `limitations` identifies
counter v2. Existing results need reanalysis; browser results do not recalculate themselves.

## Results and limits

| Input | Before | After | Verification |
| --- | ---: | ---: | --- |
| IMG_6937 | 3 | 3 | Earlier human count retained |
| IMG_6938 | 1 | 1 | Earlier human count retained |
| IMG_6939 | 1 | 1 | Earlier human count retained |
| IMG_6940 | 2 | 2 | Earlier human count retained |
| IMG_6942 | 4 | 4 | Slow rep 3 still flags; others do not |
| New live JSON | 4 | 5 | Five signal cycles; human count uncertain (5–6) |
| IMG_6943 | 5 | 19 | 19 bend/return pairs checked against matching video frames |

IMG_6943 is about 30.9 s long and starts with setup. Minima occur at 3.34, 5.08, 6.68,
8.20, 9.60, 11.14, 12.61, 14.15, 15.62, 17.13, 18.67, 20.14, 21.61, 23.01, 24.42,
25.80, 27.27, 28.67 and 30.28 s. The last return is at 30.88 s, near the file end.
This review has **not established a twentieth cycle**. Reconcile the human report before
claiming 20/20 accuracy. These inputs motivated the fix; this is development evidence.

All seven saved captures pass cumulative stability and identical final replay checks.
Identical poses through live/upload source modes produce identical reps. Original four
clips remain unflagged; 6942 retains only its rep-3 timing flag. The live JSON stays `partial`
because of trailing tracking loss. Scores remain null.

A fresh multipart request to the running API's `/api/v1/videos/analyze-with-pose` also
returned HTTP 200, 19 reps, 464 poses and 30928 ms duration. Its rep objects exactly match
the saved-pose replay. This verifies native decoding/extraction plus the actual upload
route; a fresh physical live-camera test is still separate.

425 backend tests pass, including twenty continuous synthetic cycles at 10/15/30 fps and
two sampling offsets, short turns, overlapping evidence, spikes, time-based dwell, a long
hold, tracking loss and immutable completed reps. Synthetic success is not camera accuracy.

Private extraction, traces, replays and contact sheets stay in ignored
`apps/api/artifacts/review-6943-baseline/` and root `artifacts/count-investigation/`.
Root `formcoach-live-*.json` files are now ignored too. Never commit captures or videos.

## Recheck

With the API running, from the folder containing `apps/`:

```bash
cd apps/api
.venv/bin/python -m app.tools.replay_live artifacts/review-6943-baseline/poses.json --expected-reps 19
```

That checks the reviewed 19 signal cycles, not the human estimate of 20. For new footage,
first follow VIDEO_SETUP.md, then use its independently counted number. Test a fresh physical
live set and save its JSON even on success. The reported live 9/20 still needs that check.
