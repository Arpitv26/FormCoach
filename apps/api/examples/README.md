# Live capture replay — checkpoint 4 preparation

The backend can now replay a saved set against a running API and compare its count with
your human count. Four real recordings have been checked; see [VALIDATION.md](../VALIDATION.md).
A passing synthetic replay checks software integration, not accuracy on a person.

`synthetic-pushup-capture.json` is authored geometry, not a recording. It contains 25 frames,
spaced 100 ms apart, with only the left shoulder/elbow/wrist. It represents one artificial pushup.
The expected rep runs from 600 to 2300 ms, with a minimum smoothed elbow angle of 90 degrees
at 1100 ms. Do not present these coordinates as real movement or training data.

## 1. Start the backend (Terminal 1)

Open a terminal in the repository folder containing `apps/` and run:

```bash
cd apps/api
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

Success says `Uvicorn running on http://127.0.0.1:8000`. Leave that terminal running.
If `.venv` does not exist, first follow [the API setup](../README.md).

## 2. Check the synthetic example (Terminal 2)

Open another terminal in the repository folder and run:

```bash
cd apps/api
source .venv/bin/activate
python -m app.tools.replay_live examples/synthetic-pushup-capture.json --expected-reps 1
```

The tool sends growing cumulative batches sequentially to your local backend, then repeats
the final request. It prints JSON including:

```json
{
  "outcome": "count_match",
  "expectedReps": 1,
  "observedReps": 1,
  "countMatches": true,
  "cumulativeRepsStable": true,
  "finalReplayIdentical": true
}
```

The full report also contains each snapshot's count and the final analysis with timestamps
and limitations. Scores remain null. There is no camera access or OpenAI call.

## 3. Real video first; browser captures later

The demo priority is now a prerecorded push-up video. Use [VIDEO_SETUP.md](../VIDEO_SETUP.md)
to extract poses locally; this replay tool consumes pose JSON, not video files. Computer B
is still building the frontend. Browser captures can use the same checker later. When ready,
give their agent this request:

> Read docs/API_CONTRACT.md and apps/api/examples/README.md. When browser pose tracking is
> ready, export one entire pushup set as a LiveBatchRequest JSON file using the existing
> contract. Preserve original frame timestamps, image dimensions, anatomical left/right,
> unmirrored coordinates, and landmark visibility. Include missing-pose frames rather than
> silently bridging them. Send the same cumulative frames to the live API. No schema changes.

For a first recording, choose a side view with one shoulder, elbow, wrist, hip, and ankle clearly visible.
Pause in the straight-arm top position for about a second, perform three comfortable pushups, then pause at the top for about
a second before stopping. Keep a matching local video and manually count completed reps.
An incomplete attempt is not a completed rep. Do not adjust your movement to force a score.

The exported JSON is the **whole existing request object**, not just a `frames` array:
`contractVersion`, `sessionId`, `exerciseHint: "push-up"`, `imageWidth`, `imageHeight`, `frames`,
and `isFinal`. Use set-relative milliseconds, at most 1800 frames / 120 seconds, aiming for
15 sampled frames per second. The checker treats the file as a final set even if its stored
`isFinal` is false. It preserves every pose and timestamp.

## 4. Replay the real capture

In Terminal 2, still inside `apps/api`:

```bash
mkdir -p artifacts/captures
open artifacts/captures
```

Finder opens that folder. Copy the exported JSON into it and name it `pushup-3-reps.json`.
Keep the matching video there too. The existing Git ignore rules exclude `artifacts/`.
Now run:

```bash
python -m app.tools.replay_live artifacts/captures/pushup-3-reps.json --expected-reps 3 > artifacts/captures/pushup-3-reps-report.json
cat artifacts/captures/pushup-3-reps-report.json
```

Use your actual human count after `--expected-reps`, not the count you hope the API returns.
The first command saves a report; it normally prints nothing because `>` sends output into
the file. The second displays it. Errors print in the terminal; a failed run may leave an
empty report. Captures/videos/reports stay local and should never be committed.

For a backend on a different port, append `--api-base-url http://localhost:8001`. For smaller
cumulative increments, append `--batch-frames 5`. The default is 15 new frames per request;
replay runs quickly without real-time delays, so it is not a camera latency benchmark.

## 5. Review the result before calling it accurate

| Outcome | Meaning / next action |
| --- | --- |
| `count_match` | Final measured analysis completed and its count matches; inspect each rep's timing next |
| `count_mismatch` | Inspect the matching video, intervals, and limitations; record which rep was missed/added |
| `comparison_mismatch` | Count matched, but requested timing/range flags differ; inspect `comparisonChecks` and the footage |
| `incomplete_analysis` | Tracking/readiness/unfinished movement or an old unimplemented backend prevented a complete result; even a matching count needs review |
| `Replay failed` / `Invalid capture` | Fix server startup, JSON fields, or inconsistent responses before interpreting the count |

Exit codes for scripts: 0 = complete count match and all requested flag checks match,
1 = count/flag mismatch or incomplete analysis, 2 = file, network,
validation, or response-consistency failure. An empty capture is rejected before any POST.
The report format is a local diagnostic, not a new public API contract.

Check `analysis.reps`: divide `startMs`, `endMs`, and key-moment `timestampMs` by 1000 to find
the corresponding seconds in the matching video. Smoothing delays the reported events;
record the differences rather than assuming a matching total means every rep is correct.
Check at least: a normal set, a shallow/unfinished attempt, and briefly lost tracking followed
by returning to the top position and a new rep. Keep a short local note with human count, API count, missed/extra
reps, timing differences, and visibility problems. Do not tune thresholds from one clip alone.

Stop the API with **Control+C** in Terminal 1 when finished.

## 6. Check expected comparison flags

For the pending positive timing check, first record and manually review a fixed-view set:
two similarly paced completed reps, then a noticeably slower third. Extract its poses using
[VIDEO_SETUP.md](../VIDEO_SETUP.md). Do not change timestamps or thresholds to force a flag.

For example, if you saved that extraction in `artifacts/slow-third`, run this from `apps/api`
while the API is running:

```bash
.venv/bin/python -m app.tools.replay_live artifacts/slow-third/poses.json --expected-reps 3 --expected-duration-change-reps 3 > artifacts/slow-third/replay.json
cat artifacts/slow-third/replay.json
```

This expects **exactly rep 3** to have `PUSHUP_REP_DURATION_CHANGED`. It does not check the
separate excursion rule. `comparisonChecks` lists expected/observed rep numbers, `missingReps`,
`unexpectedReps`, and `matches`. A missing flag may correctly reflect unstable reference
timing or tracking loss; inspect the supplied measurements rather than assuming a bug.

To explicitly check that a reviewed clip has **no flags of either type**, use both options
without numbers. For Computer A's existing private 6937 capture (3 human-counted reps):

```bash
.venv/bin/python -m app.tools.replay_live artifacts/recording-review/baseline/IMG_6937/poses.json --expected-reps 3 --expected-duration-change-reps --expected-excursion-reduction-reps
```

The 6937 capture is local and is not included when someone clones the repository. Use your
own extraction path and count for another clip. Omit an option to leave that rule unchecked.
Multiple expected reps are space-separated,
for example `--expected-duration-change-reps 3 6`. Numbers must be unique, at least 3, and
no greater than the human count; the rules need two preceding reference reps.

`count_match` means requested checks also matched; it does **not** mean unrequested rules
were checked. Partial analysis and count mismatches still take precedence in `outcome`;
the detailed flag checks remain available. This is a local diagnostic, with no public API
change, new pose extraction or OpenAI call. It compares declared expectations to output;
it cannot establish the recording's identity, event alignment, or movement quality.
