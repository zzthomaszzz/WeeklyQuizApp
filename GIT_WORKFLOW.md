# Team Git workflow

A shared guide for our 3-person project. Read it once, then keep the cheat sheet at the bottom open while you work.

**The one rule:** nobody ever commits directly to `main`. All work happens on a branch, and reaches `main` through a pull request that someone else approved and that CI passed.

---

## 1. One-time setup

Do this once, on your own machine.

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git config --global pull.rebase false
```

The third line makes `git pull` use merge instead of rebase. Rebase rewrites history and is a bad idea until you understand it — we're avoiding it as a team.

Clone the repo:

```bash
git clone https://github.com/<org>/<repo>.git
cd <repo>
```

Check where you are:

```bash
git status
git branch
```

`git status` is the most useful command in Git. Run it constantly. It tells you what branch you're on, what's changed, and usually what to do next.

---

## 2. Branch protection (set up once, by whoever owns the repo)

On GitHub: **Settings → Branches → Add branch protection rule** for `main`:

- Require a pull request before merging
- Require 1 approval
- Require status checks to pass (select the CI jobs once they've run once)
- Do not allow bypassing the above

This is what makes the workflow real instead of a suggestion. It also means your process is enforced rather than described, which matters for the report.

---

## 3. Branch naming

```
<type>/<short-description>
```

Types we use:

| Type | For |
|---|---|
| `feat/` | new functionality |
| `fix/` | bug fix |
| `test/` | tests only |
| `docs/` | documentation only |
| `chore/` | config, dependencies, tooling |

Examples:

```
feat/quiz-creation
feat/attempt-limit
fix/score-off-by-one
test/enrolment-service
docs/test-plan
```

Lowercase, hyphens not spaces, short. `feat/stuff` tells nobody anything.

---

## 4. The daily loop

This is the whole workflow. Six steps, repeated.

### Step 1 — Start from fresh `main`

```bash
git switch main
git pull
```

Never start a branch from a stale `main`. This one habit prevents most conflicts.

### Step 2 — Create your branch

```bash
git switch -c feat/quiz-creation
```

`-c` means create. Without it, `git switch` moves to an existing branch.

### Step 3 — Work, committing as you go

```bash
git status                    # what changed?
git add app/services/quiz.py  # stage specific files
git commit -m "Add quiz creation service"
```

Or stage everything you've changed:

```bash
git add .
git commit -m "Add quiz creation service"
```

Prefer naming files over `git add .` — it stops you accidentally committing a `.env`, a database dump, or debug prints.

**Commit small and often.** A commit per logical change, not one giant commit at the end of the week. Small commits are easier to review, easier to revert, and make the contribution history look like real work — which markers do check.

### Step 4 — Keep up with `main` (do this daily)

```bash
git fetch origin
git merge origin/main
```

If it says `Already up to date` or `Fast-forward`, carry on. If it reports conflicts, see section 8.

Daily merges = tiny conflicts. Weekly merges = a bad afternoon.

### Step 5 — Push

```bash
git push -u origin feat/quiz-creation
```

The `-u` is only needed the first time you push a branch. After that, just:

```bash
git push
```

### Step 6 — Open a pull request

On GitHub, click **Compare & pull request**. Fill in the description (template in section 6). Assign a reviewer. Wait for CI.

---

## 5. Commit messages

Format:

```
<verb in present tense> <what changed>
```

Good:

```
Add attempt limit validation to quiz service
Fix score calculation when question is skipped
Add tests for enrolment duplicate rejection
Update README with local setup steps
```

Bad:

```
fixed stuff
asdasd
update
final version 2 REAL
```

If you can't describe the commit in one line, it's probably two commits.

Optional but useful — link the issue:

```
Add attempt limit validation (#14)
```

GitHub auto-links it, which gives you free traceability between issues, commits, and PRs.

---

## 6. Pull request template

Save this as `.github/pull_request_template.md` and GitHub pre-fills every PR:

```markdown
## What this changes


## Related issue
Closes #

## How I tested it
- [ ] Unit tests added/updated
- [ ] All tests pass locally
- [ ] Manually checked in the browser

## Notes for the reviewer

```

Keep PRs **small** — under ~400 lines changed. Big PRs get rubber-stamped without real review, which defeats the point and looks bad if a marker reads the review comments.

---

## 7. Reviewing someone else's PR

Everyone reviews. Nobody merges their own PR.

Checklist:

- [ ] CI is green
- [ ] Are there tests for the new behaviour?
- [ ] Do the tests actually test something, or just assert `True`?
- [ ] Does it do what the description says, and nothing else?
- [ ] Any leftover debug prints, commented-out code, or hardcoded secrets?
- [ ] Would I understand this code in three weeks?

Leave comments on specific lines. Ask questions rather than issuing orders — "what happens if this is null?" reads better than "this is wrong."

Approve when you're happy. **Request changes** if something needs fixing — that's not an insult, it's the process working. A PR that gets change requests and then improves is exactly what the review record should look like.

To check out a teammate's branch and run it yourself:

```bash
git fetch origin
git switch feat/their-branch
```

---

## 8. Merge conflicts

Git is telling you two branches changed the same lines and it won't guess which you meant. Normal, not a disaster.

You'll see this in the file:

```
<<<<<<< HEAD
your version
=======
their version
>>>>>>> origin/main
```

Fix it:

1. Open each file `git status` lists as conflicted
2. Edit it into what the code *should* be
3. Delete all three marker lines (`<<<<<<<`, `=======`, `>>>>>>>`)
4. `git add <file>`
5. Repeat for every conflicted file
6. `git commit`
7. **Run the tests** — a merge can resolve cleanly and still be broken
8. `git push`

**Never blindly pick one side.** The right answer is often *both* changes combined. If someone added a field and someone else added a different field to the same model, you want both. If you can't tell what they intended, message them — 30 seconds of asking beats silently deleting their work.

If it's a mess:

```bash
git merge --abort
```

Puts you back exactly where you started. Nothing lost. Try again in smaller pieces, or with the other person on a call.

**Lockfiles** (`package-lock.json`, `uv.lock`) — never hand-edit. Regenerate:

```bash
git checkout --theirs package-lock.json
npm install
git add package-lock.json
```

---

## 9. Merging to `main`

Once approved and CI is green, use **Squash and merge** on GitHub.

This collapses your branch's commits into one clean commit on `main`. Keeps history readable and means your messy "wip", "fix typo", "actually fix typo" commits don't end up in the permanent record.

Then clean up locally:

```bash
git switch main
git pull
git branch -d feat/quiz-creation
```

Delete the remote branch too — GitHub offers a button right after merging.

---

## 10. When things go wrong

| Situation | Command |
|---|---|
| Undo changes to a file (not yet staged) | `git restore path/to/file` |
| Unstage a file (keeps your edits) | `git restore --staged path/to/file` |
| Fix the last commit message | `git commit --amend -m "Better message"` |
| Undo last commit, keep the changes | `git reset --soft HEAD~1` |
| Park changes to switch branches | `git stash` then `git stash pop` |
| Abort a messy merge | `git merge --abort` |
| See what happened recently | `git log --oneline -10` |
| See every move you made | `git reflog` |
| Committed to `main` by accident | see below |

**Never use `git push --force`.** It can delete a teammate's work permanently. If you think you need it, ask the group first.

**`git reflog` is the undo button.** It records every position HEAD has been in, even after resets. If you think you've destroyed work, run it before panicking — the commit is almost always still there.

**Accidentally committed to `main` locally** (before pushing):

```bash
git switch -c feat/my-work    # take the commits onto a new branch
git switch main
git reset --hard origin/main  # put main back
git switch feat/my-work
```

---

## 11. Team rules

1. Never commit directly to `main`
2. Never merge your own PR
3. Never `git push --force`
4. Never commit `.env`, secrets, or credentials — check `.gitignore` covers them
5. Merge `main` into your branch **daily**
6. Run the tests before pushing
7. Keep PRs under ~400 lines
8. If CI is red, fix it before doing anything else
9. If you're stuck for more than 20 minutes, message the group

---

## 12. Cheat sheet

```bash
# start something new
git switch main
git pull
git switch -c feat/my-thing

# work
git status
git add <files>
git commit -m "Add the thing"

# stay current (daily)
git fetch origin
git merge origin/main

# ship
git push -u origin feat/my-thing
# → open PR on GitHub → get review → squash and merge

# clean up
git switch main
git pull
git branch -d feat/my-thing
```

---

## 13. What this gives the report

Worth capturing screenshots as you go — these are hard to reconstruct at the end:

- A PR with real review comments and a requested change
- A CI run that **failed** and blocked a merge
- The branch protection settings page
- The commit history showing all three of us contributing steadily

A pipeline that has never gone red looks like it was added the night before submission. Failed builds are evidence the process was live.
