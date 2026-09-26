# Beginner setup — Mac

You need two Terminal windows. Terminal is the app where you paste commands; find it with
Command+Space, type **Terminal**, and press Enter. Paste one block at a time. Do not paste
the surrounding triple backticks. Keep the server windows open while using the app.

## 1. Find or download the repository

On the original computer, run:

```bash
cd /Users/arpit/Developer/helloHacks/helloHacks
pwd
ls
```

You should see `README.md`, `AGENTS.md`, `apps`, `contracts`, and `docs`. The outer
`/Users/arpit/Developer/helloHacks` folder is only the workspace wrapper.

On another Mac, first check Git:

```bash
git --version
```

If macOS asks to install command line developer tools, accept and wait. If needed, run
`xcode-select --install`, finish the installer, and rerun `git --version`.
Then download the shared repository (after the bootstrap is pushed):

```bash
mkdir -p ~/Developer
cd ~/Developer
git clone https://github.com/Arpitv26/helloHacks.git
cd helloHacks
ls
```

If GitHub says access is denied or repository not found, sign into the GitHub account invited
to this repository. Do not paste an access token into a source file or a clone URL. If you
already cloned, open that existing folder instead of cloning inside it again.

## 2. Check Node and npm

Node runs the frontend tools. npm downloads their packages.

```bash
node --version
npm --version
```

Use **Node 24** for both computers and CI. Successful output starts with `v24.` for Node
and a version number for npm. If Node is missing or older, open
[the official Node downloads](https://nodejs.org/en/download), select Node **24**, macOS,
and the `.pkg` installer. Open the downloaded installer, follow its steps, then close and
reopen Terminal. Repeat the two commands. Node includes npm; no separate npm download is needed.
If you already use nvm, run `nvm install` then `nvm use` in the repo; `.nvmrc` selects 24.

## 3. Check Python

Python runs the backend. Use **Python 3.12** for this project (3.13 is allowed, but 3.12 is the team default).

```bash
python3.12 --version
```

Success looks like `Python 3.12.x`. If the command is missing, open
[Python's official macOS downloads](https://www.python.org/downloads/macos/), find a
Python **3.12** release with a macOS universal2 installer, download its `.pkg`, and run it.
Reopen Terminal and retry. If the installer includes **Install Certificates.command** in
Applications → Python 3.12, double-click it. This helps Python securely download packages.

## 4. Create a private Python package folder

In Terminal 1, go to the repository root from step 1, then:

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
python --version
```

The `.venv` folder is a virtual environment: packages installed here belong to this project.
It usually adds `(.venv)` to your prompt. `python --version` should show 3.12. You create
`.venv` once; run `source .venv/bin/activate` whenever opening a new backend terminal.
Never commit `.venv` or copy it to the other Mac; each Mac creates its own.

## 5. Download backend packages and create local settings

Still in `apps/api`, with `(.venv)` active:

```bash
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

The download ends with `Successfully installed ...` or `Requirement already satisfied`.
`cp` copies the example into a private settings file named `.env`. Do this copy once;
repeating it would overwrite your local settings. Leave `OPENAI_API_KEY=` empty.

The backend reads **apps/api/.env**. The root `.env.example` is a reference, not a file
the apps automatically load. No key is needed; coaching defaults to local. Optional OpenAI setup is in apps/api/COACH_SETUP.md.
Never paste keys into Python/TypeScript files, Git commits, screenshots, or `NEXT_PUBLIC_` variables.

## 6. Start the backend

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Success includes `Uvicorn running on http://127.0.0.1:8000` and `Application startup complete`.
The terminal now stays busy serving requests; this is expected.
Open **http://localhost:8000/api/v1/health** in your browser. You should see:

```json
{"status":"ok","service":"formcoach-api"}
```

Open **http://localhost:8000/docs** to see clickable API documentation. You can expand a
route, click **Try it out**, enter the documented request, and click **Execute**.

## 7. Download frontend packages

Open a NEW Terminal window. Return to the repository root from step 1, then:

```bash
cd apps/web
npm ci
cp .env.example .env.local
```

`npm ci` downloads the exact versions recorded in `package-lock.json`. It ends with an
added/audited packages summary. The frontend reads **apps/web/.env.local**; keep its default:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The two apps run independently. Computer B can skip backend setup entirely while working
on the mock dashboard. The health check will simply report that the API is unavailable.

## 8. Start the frontend

Still in `apps/web`:

```bash
npm run dev
```

Success shows a local URL and `Ready`. Open **http://localhost:3000**.
You should see **FormCoach** with push-up upload and camera-preview choices. Open
**Connection tools** near the bottom, then **Check backend health**: it should show
`formcoach-api: ok` if Terminal 1 is running. Camera preview does not track/count movement.
For real recorded-video analysis, follow apps/api/VIDEO_SETUP.md, then open
http://localhost:3000/upload and select a push-up clip.

## 9. Stop or restart

Click the terminal running a server and press **Control+C** (not Command+C). Repeat in the
other terminal. To restart later:

```bash
# Terminal 1, starting from the repository root
cd apps/api
source .venv/bin/activate
python -m uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2, starting from the repository root
cd apps/web
npm run dev
```

Run `deactivate` after stopping the backend to leave its virtual environment.

## 10. If something goes wrong

| Symptom | Exact next step |
| --- | --- |
| `No such file or directory` for `apps/api` | Run `pwd` and `ls`; return to the folder containing `apps/`. Do not run `cd apps/api` twice. |
| `No module named fastapi` or `uvicorn` | In `apps/api`, run `source .venv/bin/activate`, then `python -m pip install -r requirements-dev.txt`. |
| `npm ci` cannot find package-lock.json | Run it in `apps/web`, not the repo root. |
| Download fails with a network error | Connect to the internet and repeat the same install command. Do not use `sudo pip`. |
| Browser cannot reach API | Open the health URL directly; check Terminal 1 is running. |
| Browser reports CORS or health button fails despite API health working | Check the web port and API URL match the settings below. Restart both servers after changing `.env` files. |
| Upload returns 503 `VIDEO_SETUP_REQUIRED` | Follow `apps/api/VIDEO_SETUP.md` to install the optional CV packages and model, then restart the API. |
| Live analysis returns `not_implemented` | Select `push-up` or legacy `squat`; other exercises/automatic selection are not implemented. |

### Port already in use

First check whether another Terminal already runs this app. Stop your old server with
Control+C. To see which program uses a port:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:3000 -sTCP:LISTEN
```

Do not kill a process you do not recognize. You can choose different ports instead:

```bash
# In apps/api with .venv active
python -m uvicorn app.main:app --reload --port 8001
```

Edit `apps/web/.env.local` in your editor to use `NEXT_PUBLIC_API_BASE_URL=http://localhost:8001`.
If port 3000 is occupied, run this in `apps/web`:

```bash
npm run dev -- --port 3001
```

Edit `apps/api/.env` to use
`CORS_ORIGINS=http://localhost:3001,http://127.0.0.1:3001` and restart the API. Open
http://localhost:3001. If Next.js automatically picks a different port, update CORS to that
port too. Environment settings are read when servers start.

## 11. Run checks before a commit

See the copy/paste **Check your work** block in the root README. Passing tests show
`passed`; lint/type checks exit without errors; the frontend build lists the homepage route.
`npm run build` checks production compilation; it does not start a server.

Before each commit, run `git status --short` at the repository root. `.env`, `.venv`,
`node_modules`, `.next`, and recordings should never appear as files to commit.
