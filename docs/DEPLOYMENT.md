# Public hackathon demo

Frontend: https://formcoach-hellohacks.vercel.app

The Next.js frontend runs on Vercel Hobby. Browser uploads go directly to the
FastAPI server on the demo Mac through ngrok HTTPS. They do not pass through a
Vercel Function. The existing 250 MiB / two-minute video limits still apply.

## Keep the demo available

The Mac must stay awake, connected to the internet, with the API and ngrok running.
Closing the lid, restarting, or stopping either process interrupts analysis and
chat; Vercel will still serve the interface. A `caffeinate` process keeps this
session idle-awake, but does not make a closed laptop an always-on server. The
ngrok process now runs as a per-user Mac LaunchAgent (`ca.formcoach.ngrok-demo`)
with automatic restart while this Mac user session is active.
The launcher also restarts on an SDK disconnect notification and checks public
API health every minute; two failed checks exit the process so LaunchAgent can
reconnect it. This catches a running process whose public tunnel has gone offline.
To reconnect immediately, use `launchctl kickstart -k gui/$(id -u)/ca.formcoach.ngrok-demo`.
For a presentation on this Mac, `http://localhost:3000` connects directly to the
local API on port 8000 and avoids the tunnel entirely.

Live sets now keep collecting the bounded joint-position history during temporary
connection errors, with a visible Reconnecting status and Last count label.
Requests retry after 2, 4, 8, then at most 10 seconds while capturing. A successful
response replaces the count using the full cumulative history. Final analysis
allows three automatic retries before preserving the set for manual retry.
Validation/contract errors still stop analysis. Reset cancels pending recovery.
The deployed UI was checked with a simulated camera and a deliberately failed
first API request: it retained 10 then 30 frames, recovered, and finalized with
HTTP 200. This checks connection recovery, not physical rep-count accuracy.

The current deployment was created from the CLI, not connected to GitHub for
automatic deployments. New Git commits do not automatically update the site.

## Vercel settings

- Project: `formcoach-hellohacks`, team `av-92ea` (Hobby).
- Root directory: `apps/web`; include source files outside that root (`contracts`).
- Framework: Next.js; Node.js 24.
- Install command: `npm ci`.
- Build command: `npm run pose:setup && npm run build` (also in `apps/web/vercel.json`).
- Production variable: `NEXT_PUBLIC_API_BASE_URL=https://pavilion-art-moistness.ngrok-free.dev`.
- Deployment protection is disabled for this public demo.

The model setup step installs the ignored browser pose model and WASM assets.
Never add an OpenAI key or ngrok token to Vercel's public frontend variables.
The frontend sends `ngrok-skip-browser-warning` only to recognized ngrok hosts;
the API allows this header for its explicitly configured origins.

## Restart on the current demo Mac

The initial deployment tools are temporary local files under
`/private/tmp/formcoach-deploy-tools`. The token is stored in the repository's
ignored `.env.ngrok`, with owner-only file permissions. Do not commit it.

If the API has stopped, open a Terminal tab:

```sh
# Tab 1: backend
cd /Users/arpit/Developer/helloHacks/helloHacks/apps/api
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://formcoach-hellohacks.vercel.app caffeinate -i .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

The ngrok LaunchAgent should restart its own process if it exits. Check it with
`launchctl print gui/$(id -u)/ca.formcoach.ngrok-demo` and test
`curl -H 'ngrok-skip-browser-warning: 1' https://pavilion-art-moistness.ngrok-free.dev/api/v1/health`. If the service is
missing after a restart and the temporary files still exist, run:

```sh
launchctl bootstrap gui/$(id -u) /private/tmp/formcoach-deploy-tools/ca.formcoach.ngrok-demo.plist
```

Do not start a duplicate tunnel while the service is running. If its URL changes,
update `NEXT_PUBLIC_API_BASE_URL` in Vercel and redeploy; the variable is
embedded at build time.

Temporary files may be removed by macOS. For a durable restart setup, install the
[official ngrok agent](https://ngrok.com/docs/getting-started/), configure your
token locally, and run `ngrok http http://127.0.0.1:8001` in place of the temporary service. Use the
URL it prints in Vercel. A different frontend domain must also be added to the
backend's `CORS_ORIGINS` before restarting the API.

## Scope and verification

This is a temporary public demo, not an independently hosted backend. ngrok free
usage quotas apply; optional OpenAI analysis uses the existing backend account
and is not made free by this hosting setup. Uploaded recordings and credentials
were excluded from the frontend deployment.

On September 27, 2026, a 221 MiB original MOV uploaded through the public tunnel
returned HTTP 200 in approximately 121 seconds, with six detected lat-pulldown
reps, a pose track, and completed AI visual review. This checks the upload path,
not general counting accuracy or performance on every connection.
