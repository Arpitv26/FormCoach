# FormCoach: technical briefing for the backend presenter

**Use this as context in ChatGPT:** “Help me make a simple architecture slide, a 60–90 second backend explanation, and judge Q&A for FormCoach. Ground every claim in this briefing. Separate implemented behavior from limitations. Explain technical ideas in words I can say aloud. Ask me before adding claims about accuracy, safety, or features.”

This briefing reflects `main` on September 27, 2026. Older roadmap notes in the repo can be historical; the actual code and the current checkpoints below take priority. You own the backend/architecture part of the pitch. The live demo focuses on push-ups; uploads support push-ups, incline dumbbell bench press, cable lateral raise and lat pulldown. Squats have a legacy counter but are not the pitch focus.

## One-sentence explanation

FormCoach turns a camera recording into body landmarks, runs **our own exercise-specific rules** to identify completed reps and measurements, then presents the evidence with video playback and an optional AI coach.

## Architecture slide: draw these boxes and arrows

```text
PHONE / BROWSER (Next.js + React)
  ├─ Live webcam → MediaPipe in browser → timestamped PoseFrames ─┐
  └─ Video upload → Python API → OpenCV + MediaPipe → PoseFrames ───┤
                                                                 ↓
PYTHON API (FastAPI + Pydantic)
  Both paths → shared RuleBasedAnalyzer → visibility checks → 2D joint angles
             → exercise-specific phase/rep logic → counts, times, measurements
                                                        ↓
  AnalysisResponse v1.0 + optional upload pose track → browser results/playback
                                                        ↓
  Optional: sampled upload images → OpenAI visual review → labeled observations
  Optional: analysis evidence + user question → OpenAI conversational coach
  Saved summaries → browser localStorage (no server database)
```

**The key design choice:** Both input routes normalize the provider's output into FormCoach's `PoseFrame` (timestamp, frame index, up to 33 named landmarks with normalized coordinates and visibility). The analyzer sees the same format regardless of whether a pose came from a webcam or an uploaded clip. The pretrained MediaPipe model estimates body joints; **we did not train a pose model**. Our contribution is the normalized contract, geometric analysis, counting policies, evidence handling, coaching integration and interface.

## What happens when someone uploads a clip

1. Browser sends the selected exercise ID and original MP4/MOV/WebM to `POST /api/v1/videos/analyze-with-pose`. Selecting an exercise is **not automatic exercise recognition**.
2. The API checks type/size, temporarily copies the file, decodes frames, estimates poses with MediaPipe, and maps provider landmarks into `PoseFrame`. The limit is **250 MiB, 2 minutes**, at most 1,800 sampled pose frames. One upload extraction runs per API process; another simultaneous upload receives a busy response.
3. The shared analyzer checks needed joints, image boundaries and visibility. It restores the original image aspect ratio before calculating 2D angles; otherwise portrait video would distort them. It locks onto one anatomical side during a set instead of swapping sides when tracking is lost.
4. The exercise policy looks for a **sequence of phases**, not one frame. For push-ups, the current counting heuristic confirms a top position, descent, a bent elbow, ascent and return. It uses a three-sample median, sustained raw observations, separate thresholds for entering/leaving phases, and tracking-gap rules. The current push-up return and bend zones are 150° and 100° elbow angles, with 60 ms raw confirmation. These are engineering counting thresholds, **not ideal-form or medical standards**. Gym exercises have separate rules.
5. The response includes completed reps, start/end times, angle/timing measurements, timeline events, limitations and the sampled pose track. The browser overlays the skeleton and lets people jump to cited moments. Scores are `null`; there is **no calibrated form grade**.
6. If enabled, a separate visual review sends up to 64 sampled JPEG frames to OpenAI. Its observations and cues are labeled AI interpretation with real frame timestamps. It cannot change the algorithmic rep count or angle measurements. A review failure leaves measured results available. The chat receives measurements and visual findings, not the video again.

**Live route:** The browser estimates poses locally, keeps at most 10 frames per second and sends a cumulative short-set snapshot roughly every second to `POST /api/v1/live/analyze-batch`; the final snapshot marks the set complete. The server is stateless: no session database or hidden incremental counter. The browser draws the live skeleton; Python owns rep decisions. Live currently targets push-ups, and a fresh physical camera accuracy check remains separate from tests and recorded-clip checks.

## How to explain the AI honestly

There are **two different jobs**. The deterministic analyzer counts and measures from landmarks. Optional OpenAI visual review interprets sampled video images for things landmark geometry cannot establish reliably, such as visible torso rocking in a pulldown; this is not continuous-video understanding. Optional chat uses the structured measurements and labeled findings to answer a user's question. The backend keeps the key; the browser never gets it. Without the optional provider, local summary/next-set guidance still works; free-form chat is limited. Correct timestamps and structured JSON do not prove that an AI observation is true, so playback stays available for checking.

## Evidence, limitations and likely judge questions

| Judge asks | Short answer you can say |
| --- | --- |
| “What did you actually build?” | “We use pretrained MediaPipe for landmark detection. We built the shared pose contract, exercise-specific rep logic, geometric measurements, API, evidence handling and user-facing review.” |
| “Is this just a prompt to an AI model?” | “No. Rep counting and timestamps come from our Python analyzer on pose landmarks. AI is optional and separately labeled for visual observations and explanation.” |
| “How do you count a rep?” | “We track a joint angle through a complete sequence of positions over time. The thresholds, smoothing and tracking rules prevent one noisy frame from becoming a rep.” |
| “How accurate is it?” | “We have development checks on recorded clips, not an independent accuracy study. For example, the public demo analyzed a 221 MiB pulldown clip and returned six detected reps with playback. Other views can miss reps; a changed pulldown returned five of six reported, and back-view lateral raises have failed. We show limits rather than claim a global accuracy number.” |
| “Does it judge good or bad form?” | “It measures visible 2D motion and can give timestamped, labeled visual observations. There is no validated universal form score or injury prediction.” |
| “Why do counts fail?” | “Occlusion, multiple people, poor view, missing joints, or a movement that does not meet the current phase rules can break a count. We cannot infer the exact cause of a missed rep from counted-rep data alone; review the matching video.” |
| “Why a shared pose format?” | “It lets live and uploaded footage use one analyzer, makes the model provider replaceable, and gives frontend/backend a versioned API contract.” |
| “How do you validate it?” | “Geometry and phase logic have synthetic boundary tests; prerecorded clips are compared with human-reviewed frames; HTTP and browser tests exercise the real flow. The footage used to tune rules is development evidence, not unbiased validation.” |
| “What about privacy?” | “The API processes uploads in temporary storage and deletes its copy. Browser saved sets contain summaries, not video or raw pose tracks. Optional visual review sends sampled images to OpenAI when enabled and disclosed; provider retention follows the account's terms.” |
| “How is it deployed?” | “The Next.js frontend is on Vercel. Browser uploads go directly through ngrok to FastAPI on the demo Mac, avoiding Vercel's request-body limit. That is temporary hackathon hosting; the Mac must remain awake and connected.” |
| “What would you build next?” | “More independent footage and trainer review first, especially failed camera views and physical live tests. Then improve calibration and deploy a persistent backend before considering a trustworthy form score.” |

## Suggested spoken technical segment (about 65 seconds)

“My part was the backend and the analysis architecture. The camera itself gives us pixels, so we use Google's pretrained MediaPipe model to estimate body landmarks. For an uploaded clip we extract those landmarks in Python; for live push-ups the browser extracts them. Both become the same timestamped pose format, which means one analyzer can handle either input.

Our analyzer checks whether the joints are actually visible, computes 2D angles with the camera's aspect ratio accounted for, then follows exercise-specific movement phases to count completed reps. It returns the count, rep timing and supporting measurements with timestamps, so you can inspect the exact moment on the original video. We keep unsupported measurements unknown instead of inventing a score.

We also added an optional AI layer. It reviews sampled upload frames for labeled observations and lets the coach explain those observations alongside the measured results. AI never overwrites the rep count. The important limit is that this is a 2D, view-dependent demo: some angles and occluded movements cannot be assessed reliably. Our next step is broader footage and trainer validation.”

## Source map if ChatGPT or a judge wants depth

- Architecture and API contract: `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, `contracts/README.md`.
- Actual HTTP boundaries: `apps/api/app/api/routes/{videos,live,coach}.py`.
- Pose extraction/limits: `apps/api/app/services/{mediapipe_pose,video_processor}.py`.
- Shared analyzer and exercise rules: `apps/api/app/analysis/movement.py`, `apps/api/app/analysis/exercises/`, `apps/api/COUNTING.md`, `apps/api/GYM_EXERCISES.md`.
- AI and safeguards: `docs/AI_COACH.md`, `apps/api/app/services/{visual_review,conversation_coach}.py`, `docs/SAFETY.md`.
- Browser live/session/saved summaries: `apps/web/src/lib/{live/session,api/client,log/store}.ts`.
- Current public setup: `docs/DEPLOYMENT.md`.

**Slide instruction:** use 5–7 boxes: inputs → pose extraction → normalized frames → rule-based analyzer → results/playback, with a visibly separate optional AI branch. Put “2D, view-dependent; no calibrated form score” in a small limitations footer. Avoid a database icon because saved summaries currently live in browser storage.
