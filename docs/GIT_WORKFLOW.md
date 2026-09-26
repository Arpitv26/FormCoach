# Two-computer Git workflow

Git records snapshots called commits. A branch is a named line of work. `main` is the shared
starting point; `origin` is the GitHub copy. A local commit is not on the other computer until
it is pushed to GitHub and the other computer pulls it.

Run all commands from the repository root: the folder containing `apps/` and AGENTS.md.
On the original machine it is `/Users/arpit/Developer/helloHacks/helloHacks`.
On a fresh clone it is normally `~/Developer/helloHacks`.

## Before both people begin

The bootstrap must be committed on `main` and pushed to `origin/main`. If it has only been
committed locally, Computer A runs `git push origin main` first. Both computers should run
`git log -1 --oneline` after pulling and confirm the same bootstrap commit.
Do not start both roles on main, copy node_modules/.venv between Macs, or start redesigning contracts.

If needed, set your own Git identity (replace the two example values with your own):

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

## Computer A — backend branch

```bash
git checkout main
git pull --ff-only
git checkout -b backend-cv
```

`checkout main` switches to the shared branch. `pull --ff-only` downloads its latest commits
without making an unexpected merge. `checkout -b` creates and switches to your new branch.
`git branch --show-current` should print `backend-cv`.

Own `apps/api/**`, backend tests, CV, movement analysis, and AI integration.

## Computer B — frontend branch

```bash
git checkout main
git pull --ff-only
git checkout -b frontend
```

`git branch --show-current` should print `frontend`. Own `apps/web/**`, including webcam,
product interface, results, charts, and polish. Work from mock data while A builds analysis.

If Git says the branch already exists, use `git checkout backend-cv` or `git checkout frontend`
instead of creating it again. If checkout says local changes would be overwritten, stop and
commit your current work; do not use `git reset --hard` to make the message disappear.

## Everyday work

Make a small working improvement, run your app's checks, inspect changes, then commit:

```bash
git status --short
git diff
# Computer A stages their own directory:
git add apps/api
git diff --cached
git commit -m "feat(api): add tested squat angle helpers"
git push -u origin backend-cv
```

Computer B uses:

```bash
git status --short
git diff
git add apps/web
git diff --cached
git commit -m "feat(web): add mock results dashboard"
git push -u origin frontend
```

The first push with `-u` connects your local branch to GitHub; later use `git push`.
Commit frequently at working checkpoints. Good later messages include
`test(api): cover missing landmarks`, `feat(web): add worst-rep timeline jump`, and
`docs: clarify live frame timestamps`. Do not stage `.env`, recordings, or dependencies.

## Shared changes

Shared files: `contracts/**`, `docs/**`, `scripts/**`, `.github/**`, root config, README.md,
AGENTS.md. Changes should be small and deliberate. Do not both edit them at the same time.

1. Tell the other developer what must change and why.
2. Make one isolated commit with docs, models, schemas, examples, and generated types together.
3. Review it together and merge the shared contract change into main before either branch relies on it.
4. Bring main into both branches using the commands below.

Do not cherry-pick the same shared change and independently rewrite it in both branches.
Agree who owns it and use the shared main commit.

## Integrate finished work

Push your branch, open the GitHub repository, click **Compare & pull request**, select
`main` as the destination, describe what works and which checks passed, and ask your teammate
to review. A pull request is a review page for your proposed commits. Merge after checks pass.
Avoid editing the other person's app in your pull request.

After a merge, bring the shared changes into your own branch. First commit any local work.
For Computer A:

```bash
git checkout main
git pull --ff-only
git checkout backend-cv
git merge main
```

For Computer B:

```bash
git checkout main
git pull --ff-only
git checkout frontend
git merge main
```

Run checks again after integration. Do not force-push main or rewrite commits others use.
If `pull --ff-only` fails, your local main has diverged: inspect `git status` and
`git log --oneline --graph -10` with your teammate before choosing a fix.

## If Git reports a conflict

Run `git status` to see the affected files. Ask the owner of each file to help. An editor
shows conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`); choose or combine the intended
code, remove markers, run checks, then `git add` only the resolved files and `git commit`.
Do not blindly choose “ours” or “theirs” for a contract file. To cancel the current merge
while deciding, use `git merge --abort`; your pre-merge committed work remains.
