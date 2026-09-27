# Try the coach — Computer A

The local coach already works without an account or key. It summarizes supplied measurements.
The current UI uses optional OpenAI conversational replies grounded in supplied evidence.
Upload visual review can also send sampled images to OpenAI. Read ../../docs/AI_COACH.md.

## 1. Start the backend with local coaching

Open Terminal. On this Computer A, copy these commands:

```bash
cd ~/Developer/helloHacks/helloHacks/apps/api
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

If you cloned elsewhere, use that clone's `apps/api` folder. If `.venv` is missing, first
follow ../../docs/BEGINNER_SETUP.md. Success includes `Uvicorn running on http://127.0.0.1:8000`.
Keep this terminal open. Stop it later with **Control+C**.

## 2. Test without needing the frontend

Open a second Terminal window and paste:

```bash
cd ~/Developer/helloHacks/helloHacks/apps/api
source .venv/bin/activate
python - <<'PY'
import json
from pathlib import Path
from urllib.request import Request, urlopen
analysis = json.loads(Path('../../contracts/examples/pushup-comparison-analysis.json').read_text())
body = json.dumps({'analysis': analysis, 'mode': 'summary'}).encode()
request = Request('http://localhost:8000/api/v1/coach', data=body,
                  headers={'Content-Type': 'application/json'})
with urlopen(request, timeout=15) as response:
    result = json.load(response)
print('Provider:', result['provider'])
print(result['message'])
print('Evidence:', result['evidence'])
print('Limitations:', '\n'.join(result['limitations']))
PY
```

Expect `Provider: fallback`, `Demo data only`, three completed reps, and details about rep 3.
This file is synthetic. To use your saved real result, change only the `analysis = ...` line
with the path to an actual **AnalysisResponse JSON** saved from `/videos/analyze`.
Replay reports wrap it in `analysis`, so those require `json.loads(...)["analysis"]`.
Chat explains the attached analysis; optional upload review supplies visual findings first.

## 3. Optional: enable OpenAI

This step can spend API credits. Leave the default fallback on if you don't want that yet.
In the second terminal:

```bash
python -m pip install -r requirements-coach.txt
cp -n .env.example .env
open -e .env
```

`cp -n` creates the private settings file only if it doesn't exist; it preserves an existing
file. TextEdit opens it. Keep any existing CORS/model-path lines. Add or edit these lines,
with each name appearing only once:

```dotenv
COACH_PROVIDER=openai
OPENAI_MODEL=gpt-4.1-mini-2025-04-14
OPENAI_API_KEY=
```

For the richer upload review requested on Computer A, also set:

```dotenv
VISUAL_REVIEW_ENABLED=true
OPENAI_VISION_MODEL=gpt-5.4-2026-03-05
OPENAI_MODEL=gpt-5.4-2026-03-05
```

Keep only one `OPENAI_MODEL` line. This sends up to 64 sampled JPEGs per analyzed upload to
OpenAI and spends credits. Restart the backend after changing settings, then analyze the clip
again; old results do not acquire visual findings automatically. Successful results include
“What the visual review noticed” with playback links. A failed review leaves counts usable.

Paste your key **after the last equals sign in TextEdit only**, save with Command+S, close
TextEdit. Do not paste it into chat, source files, screenshots, Git, or any `NEXT_PUBLIC_`
variable. The real `.env` is ignored by Git. You obtain the key from your own OpenAI API
account; ChatGPT subscription access does not configure this backend.

Restart the first terminal's server: press Control+C, then run:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Repeat step 2 once. Success is `Provider: openai` with evidence-backed, demo-labeled wording.
If it says `fallback`, read the limitations: the app stays usable. Check the three local
settings, optional package install, account API access/credits, and network. Never post your
key to debug this. An inaccessible model or rate limit also falls back; errors are sanitized.
To turn paid calls off, set `COACH_PROVIDER=fallback`, save, and restart.

## 4. Ask a supported question

In the step 2 script, replace the `body = ...` line with:

```python
body = json.dumps(
    {"analysis": analysis, "mode": "qa", "question": "How long did rep 3 take?"}
).encode()
```

With working OpenAI access, expect measured timing and its evidence paths. Without OpenAI,
QA explicitly says it is unsupported. Unsupported medical/form-quality questions must not
produce a diagnosis or invented finding. This coach has no conversation history.

## Checks for backend changes

```bash
python -m pytest -q tests/test_coach.py tests/test_routes.py
python -m ruff check app/services/coach_evidence.py app/services/openai_coach.py tests/test_coach.py
```

Tests make no real OpenAI calls. SDK HTTP tests use an in-process fake server transport.
The SDK-specific tests skip if the optional package is absent; CI installs it to exercise them.
