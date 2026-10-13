# Defect Register

Factual record of defects found during development of the Weekly Quiz App.
Each entry records what was wrong, how it was detected, and what was done
about it, with a commit or PR reference so every claim can be checked against
the repository.

**Severity** — impact if it reached production.
**Priority** — how soon it needed fixing relative to other work.

| | Severity | Priority |
|---|---|---|
| **S1 / P1** | Security hole, data loss, or the app cannot run | Fix before anything else |
| **S2 / P2** | A feature is broken or a quality control is ineffective | Fix before the next merge |
| **S3 / P3** | Incorrect behaviour with a workaround, or blocks onboarding | Fix this sprint |
| **S4 / P4** | Cosmetic, documentation, or tidiness | Fix when convenient |

**Status** — Open, Fixed, or Closed (fixed and verified by a test or review).

**Detection method** categories used below: Code review, Automated test,
Manual testing, Static inspection, Merge conflict, Runtime failure.

---

## Summary

| ID | Title | Severity | Detection | Status |
|---|---|---|---|---|
| D-01 | Test assertion never executed | S2 | Static inspection | Closed |
| D-02 | Quiz update had no authorisation | S1 | Code review | Closed |
| D-03 | Duplicated application block in `main.py` | S3 | Static inspection | Closed |
| D-04 | Two parallel authentication implementations | S2 | Static inspection | Closed |
| D-05 | Auth dependency broken by model change | S1 | Static inspection | Open |
| D-06 | Required setting introduced by conflict resolution | S1 | Merge conflict | Open |
| D-07 | Frontend could not reach the backend | S2 | Manual testing | Closed |
| D-08 | Dead health code in `auth.py` | S4 | Static inspection | Closed |
| D-09 | Seed data unusable by other developers | S3 | Static inspection | Open |
| D-10 | Integration tests undocumented and unrunnable | S3 | Static inspection | Open |
| D-11 | `max_attempts` specified but not implemented | S2 | Static inspection | Open |
| D-12 | Lint quality gate is inert | S2 | Static inspection | Open |
| D-13 | Branch merge would have deleted a working route | S2 | Code review | Closed |
| D-14 | Documented Python version does not match the build | S4 | Static inspection | Open |
| D-15 | Test dependencies shipped to production | S3 | Code review | Open |

---

## D-01 — Test assertion never executed

**Severity** S2 **Priority** P2 **Status** Closed

**Introduced** `a7580d6`, 2026-08-05, in the first Vitest setup.

**Defect.** `web/src/First.test.tsx` contained:

```js
expect(true).toBeTruthy
```

The matcher was referenced but never called — no parentheses. The assertion
never ran. The test also asserted on the literal `true` rather than on
anything the component produced, so it could not fail under any circumstance.

**Detection.** Static inspection during a code reading session, 2026-08-28.
It survived CI and a human review on PR #2 because the test *passed* and a
passing test was taken as evidence of a working test.

**Technical cause.** JavaScript allows a property to be referenced without
invoking it, and this is valid at runtime. No linting was configured, and the
project's ESLint packages were installed without a config file, so no rule
checked for uninvoked matchers.

**Fix.** `60360cb`, PR #23 — `First.tsx` and `First.test.tsx` deleted. Both
were scaffolding used to prove the Vitest harness worked; by then real
component tests existed.

**Detection gap.** The review checklist asks "are there tests for the new
behaviour?" but not "does the test fail when the behaviour breaks?". No lint
rule was active. `eslint-plugin-jest-dom` detects this specific error class.

---

## D-02 — Quiz update had no authorisation

**Severity** S1 **Priority** P1 **Status** Closed

**Introduced** `288f132`, 2026-10-08, PR #24.

**Defect.** `PATCH /api/quizzes/{quiz_id}` accepted changes to a quiz's title,
status, and opening and closing times with no check on who was asking. Any
request that knew or guessed a quiz id could alter it, including publishing a
draft or reopening a closed quiz.

**Detection.** Code review on PR #24 by platinumwolaopo:

> "quzz_id does not check user. User can change title, open time if he knows
> the quiz id. Better add limit."

**Technical cause.** The endpoint was written as a data operation without an
authorisation step. At the time the branch was written no shared
`current_user` dependency existed, so adding one was not a one-line change and
was deferred.

**Fix.** `06f18e0`, 2026-10-12 — role check (lecturer only), plus an ownership
check joining `quizzes` to `courses` and comparing `lecturer_id` to the
authenticated user id. A non-owning lecturer now receives 403.

**Detection gap.** No automated test covered the negative case. A human caught
it; CI could not have. PR #24 still has no tests at time of writing.

---

## D-03 — Duplicated application block in `main.py`

**Severity** S3 **Priority** P3 **Status** Closed

**Introduced** `bf5dcdf`, 2026-09-05, merging `main` into
`chores/backend-routers`.

**Defect.** `api/app/main.py` contained two complete application setups: two
import blocks, two `app = FastAPI(...)` assignments, and two
`add_middleware` calls. The second assignment replaced the first, so roughly
twenty lines at the top of the file were unreachable.

**Technical cause.** A merge conflict resolved by keeping both sides. Because
Python permits rebinding a name, the result was syntactically valid and ran
correctly, so neither CI nor manual testing registered a problem.

**Detection.** Static inspection while reviewing the backend structure,
2026-09-16. It had been on `main` for eleven days.

**Fix.** `df43e59`, PR #25 — `main.py` rewritten with a single application
setup.

**Detection gap.** Automated tests verify behaviour, and the behaviour was
correct. Dead code of this kind is only visible to a reader or a linter. No
Python linting runs in CI, though `ruff` is listed in `requirements-dev.txt`.

---

## D-04 — Two parallel authentication implementations

**Severity** S2 **Priority** P1 **Status** Closed

**Introduced** between 2026-09-09 and 2026-09-10, on branches
`feat/authentication-api` (PR #18) and `dashboard` (PR #19).

**Defect.** Two branches implemented login independently and concurrently.
They conflicted in five backend files and used incompatible session models:
one returned a JWT in the response body for the client to store, the other
set an httpOnly cookie. Neither could merge without discarding part of the
other.

**Detection.** Static inspection, 2026-09-16, comparing open branches with
`git merge-tree`, which reported five conflict points between them.

**Technical cause.** Work was assigned by feature area rather than by
interface, and no one declared ownership of authentication before starting.
Both branches then ran for roughly a month without merging `main`.

**Fix.** PR #25 — a single implementation combining both: the layered
router/service/repository structure and cookie sessions from `dashboard`, the
registration endpoint, Pydantic validation schemas, and tests from
`feat/authentication-api`. PR #18 was closed; PR #19 was re-cut as
frontend-only PR #26.

**Detection gap.** Nothing in the workflow surfaces two branches editing the
same files. The documented daily `git merge origin/main` would have exposed
the collision within a day; neither branch did it.

---

## D-05 — Auth dependency broken by model change

**Severity** S1 **Priority** P1 **Status** Open

**Present on** branch `feat/quiz-api` (PR #24).

**Defect.** `api/app/routers/quizzes.py` defines its own `get_current_user`
built on `HTTPBearer` and `jwt.decode(..., settings.jwt_secret_key)`. After
PR #25 the application issues httpOnly cookie sessions and has no
`jwt_secret_key` setting. Once `main` is merged into that branch, every
protected quiz endpoint will reject every real request, because nothing issues
the Bearer tokens it expects.

**Detection.** Static inspection, 2026-10-13, while assessing what PR #24
needed after PR #25 merged.

**Technical cause.** The branch was written against an auth model that was
later replaced on `main`. The branch has been behind `main` for six commits
and has not merged it back.

**Proposed fix.** Delete the local `get_current_user` and the `HTTPBearer`
import; import `current_user` from `app.routers.auth`, which returns the same
`{id, email, name, role}` shape so call sites are unchanged.

**Detection gap.** PR #24 has no tests, so CI reports success on a branch
whose authorisation cannot work. This is the same gap as D-02 on the same
branch.

---

## D-06 — Required setting introduced by conflict resolution

**Severity** S1 **Priority** P1 **Status** Open

**Latent in** the conflict between `feat/quiz-api` and `main`.

**Defect.** `feat/quiz-api` adds `jwt_secret_key: str` to `Settings` with no
default, making it mandatory at startup. `main` no longer uses it. Resolving
the `api/app/config.py` conflict by accepting both sides produces an
application that raises a Pydantic `ValidationError` on import and cannot
start, because no environment anywhere sets `JWT_SECRET_KEY`.

**Detection.** Static inspection of the four pending conflicts, 2026-10-13,
before any merge was attempted.

**Technical cause.** A setting was introduced for an authentication approach
that was subsequently abandoned, and the natural conflict resolution
("keep both") preserves it.

**Proposed fix.** Delete all three `jwt_secret_key` / `JWT_SECRET_KEY` lines
from `config.py`, `.env.example`, and `ci.yml` rather than merging them.

**Detection gap.** This is a defect that would be *created* by the merge, not
one that exists in either branch alone. No automated check examines the result
of a conflict resolution before it is committed.

---

## D-07 — Frontend could not reach the backend

**Severity** S2 **Priority** P2 **Status** Closed

**Present from** project start until `31c1e5a`, 2026-08-06.

**Defect.** `App.tsx` called `fetch('/api/health')`. Being a relative URL, the
browser resolved it against the page's own origin, `localhost:5173`, which is
the Vite dev server. Vite returned `index.html` for the unknown path,
`response.json()` failed to parse HTML, the `.catch` branch ran, and the page
displayed "API: failed". The FastAPI server on port 8000 was never contacted.

**Detection.** Manual testing — the page showed `failed` instead of `ok`.

**Technical cause.** No `server.proxy` entry in `vite.config.ts`. The relative
URL is correct for production, where both are served from one origin on
Vercel, but requires a dev proxy locally.

**Fix.** `31c1e5a`, PR #4 — proxy added forwarding `/api` to
`http://127.0.0.1:8000`. `127.0.0.1` rather than `localhost` because Node
resolves `localhost` to IPv6 `::1` on Windows while uvicorn binds IPv4.

**Detection gap.** No test covered the dev configuration, and none reasonably
could — this is an environment defect, caught by running the application.

---

## D-08 — Dead health code in `auth.py`

**Severity** S4 **Priority** P4 **Status** Closed

**Introduced** `8df1ea2`, 2026-09-05, splitting routers into separate files.

**Defect.** `api/app/routers/auth.py` contained a complete copy of the health
endpoints — `tags=["health"]`, `/health`, and `/health/database` — and no
authentication code. Nothing imported it. A second copy of the same routes
lived in `health.py`.

**Detection.** Static inspection, 2026-09-16.

**Technical cause.** The file was created by copying `health.py` as a starting
point and the contents were never replaced.

**Fix.** `df43e59`, PR #25 — `auth.py` replaced with the real authentication
router; `/health/database` consolidated into `health.py`.

**Detection gap.** Unreferenced code produces no test failures and no runtime
error. Only a reader or a dead-code linter finds it.

---

## D-09 — Seed data unusable by other developers

**Severity** S3 **Priority** P3 **Status** Open

**Introduced** `d897152`, 2026-09-24, PR #21.

**Defect.** `api/database/seed.sql` inserts into `courses`, `enrolments`,
`quizzes`, `questions`, `options`, `attempts`, and `answers`, but not `users`.
Its header reads:

> `-- Run seed-users.local.sql first to create the sample accounts.`

`seed-users.local.sql` is listed in `.gitignore` and is not in the repository.
`courses.lecturer_id`, `enrolments.student_id`, and `attempts.student_id` are
all `NOT NULL` foreign keys to `users(id)`, so running `seed.sql` on a fresh
database fails on the first insert.

**Detection.** Static inspection of the seed file against the schema,
2026-10-13.

**Technical cause.** User rows contain password hashes, so the author
correctly kept them out of version control — but no committed substitute was
provided, and no instructions describe how to create one.

**Proposed fix.** Commit a `seed-users.example.sql` containing accounts with
hashes of a known throwaway password, or add a short script that calls
`POST /api/auth/register` to create the sample accounts.

**Detection gap.** Nothing runs the seed file in CI, so it has only ever been
executed on the machine where it was written.

---

## D-10 — Integration tests undocumented and unrunnable

**Severity** S3 **Priority** P3 **Status** Open

**Present since** `1139bd1`, 2026-09-05.

**Defect.** `api/tests/conftest.py` reads `TEST_DATABASE_URL` from
`api/.env.test` and raises `RuntimeError` if it is missing. `.env.test` is
gitignored, is absent from `.env.example`, and is not mentioned in the README.
A new team member following the README's documented command
(`cd api && .venv/Scripts/pytest.exe`) gets a `RuntimeError` rather than a
test run.

The README is also now out of date: it gives a single pytest command, while CI
runs `unit_tests` and `tests` as separate suites.

**Detection.** Static inspection while adding the backend CI job, 2026-08-19;
the README inaccuracy was introduced later by PR #25 and found on 2026-10-13.

**Technical cause.** The setting was added to the test harness without a
matching entry in the example environment file or the setup documentation.

**Proposed fix.** Add `TEST_DATABASE_URL` guidance and a `.env.test` step to
the README, and correct the test commands to match CI.

**Detection gap.** CI supplies `TEST_DATABASE_URL` from a repository secret,
so the pipeline passes while a fresh local checkout fails. No check verifies
that the documented setup instructions actually work.

---

## D-11 — `max_attempts` specified but not implemented

**Severity** S2 **Priority** P2 **Status** Open

**Present since** project start.

**Defect.** `CLAUDE.md` states "Quizzes have max_attempts (NULL = unlimited)"
as a domain rule. The `quizzes` table in `api/database/schema.sql` has no such
column, and no code enforces an attempt limit. A student can submit unlimited
attempts at any quiz.

**Detection.** Static inspection comparing the stated requirements against the
schema, 2026-09-28.

**Technical cause.** A requirement recorded in project documentation was never
carried into the schema or the implementation.

**Proposed fix.** Add the column, then enforce it in the attempt submission
service. `AttemptRepository.attempts_taken()` exists for this purpose.

**Detection gap.** No traceability existed between the documented requirements
and the implementation, so a requirement could be stated and silently never
built.

---

## D-12 — Lint quality gate is inert

**Severity** S2 **Priority** P2 **Status** Open

**Present since** the initial scaffold, 2026-08-04.

**Defect.** `web/package.json` contains `"lint": ""`. Running `npm run lint`
exits successfully having done nothing. No `eslint.config.js` exists anywhere
in the repository, though `eslint`, `typescript-eslint`,
`eslint-plugin-react-hooks` and `eslint-plugin-react-refresh` are all
installed. `ruff` is similarly listed in `requirements-dev.txt` and never run.

The review checklist in `GIT_WORKFLOW.md` assumes linting is part of the
quality gate.

**Detection.** Static inspection, 2026-08-04.

**Technical cause.** The Vite scaffold's ESLint config was removed and the
script blanked, leaving the dependencies in place. A script that exits 0
without running anything is indistinguishable in CI from one that passes.

**Proposed fix.** Restore a flat ESLint config, point the script at it, and
add a lint step to the CI job. `eslint-plugin-jest-dom` would additionally
have caught D-01.

**Detection gap.** This is the defect that allowed D-01 to survive. An empty
quality gate is worse than an absent one, because it appears to be working.

---

## D-13 — Branch merge would have deleted a working route

**Severity** S2 **Priority** P1 **Status** Closed

**Latent in** the `dashboard` branch (PR #19).

**Defect.** `dashboard` was branched on 2026-09-10, before the developer team
page merged on `main`. Its `web/src/App.tsx` therefore contained a route table
with no `/dev` entry. Merging the branch's version of that file would have
silently removed a working page from the application.

The same branch would also have restored `First.tsx` and `First.test.tsx`,
deleted in PR #23 (see D-01).

**Detection.** Code review while re-cutting the branch as PR #26, 2026-10-13 —
noticed by comparing the branch's `App.tsx` against `main`'s before copying it
across.

**Technical cause.** A long-lived branch carrying a whole-file copy of a file
that changed on `main` meanwhile. Git would have reported no conflict, because
only one side changed the file after the branch point.

**Fix.** PR #26 — route tables merged by hand, keeping `/dev`; the deleted
scaffold files left deleted.

**Detection gap.** No test asserted that `/dev` renders. A route test would
have turned a silent deletion into a failing build. This is the most dangerous
class of defect found: a merge that is clean, compiles, passes tests, and
still removes a feature.

---

## D-14 — Documented Python version does not match the build

**Severity** S4 **Priority** P4 **Status** Open

**Defect.** `CLAUDE.md` specifies Python 3.12. The virtual environment is
3.13.14, `README.md` says 3.13, and CI pins `python-version: '3.13'`. Vercel's
supported Python runtime has not been verified against either.

**Detection.** Static inspection while writing the README, 2026-08-06.

**Technical cause.** The stack was recorded during planning and the
environment was later created with a different version; the document was not
revisited.

**Proposed fix.** Decide the supported version, confirm it against the Vercel
runtime, and make all three sources agree.

---

## D-15 — Test dependencies shipped to production

**Severity** S3 **Priority** P3 **Status** Open

**Introduced** `4104f3e`, 2026-08-07.

**Defect.** `api/requirements.txt`, the production dependency list deployed as
a Vercel function, contains `pytest`, `pytest-asyncio`, and `httpx`. All three
are already present in `requirements-dev.txt`. Test frameworks are installed
into the production runtime, increasing the deployment size and cold-start
time, and enlarging the installed surface area.

**Detection.** Code review while adding the backend CI job, 2026-08-19.

**Technical cause.** Dependencies were added to the first requirements file
rather than the development one.

**Proposed fix.** Remove the three test packages from `requirements.txt`.

---

## Detection method tally

| Method | Count | Defect IDs |
|---|---|---|
| Static inspection | 10 | D-01, D-03, D-04, D-05, D-08, D-09, D-10, D-11, D-12, D-14 |
| Code review | 3 | D-02, D-13, D-15 |
| Manual testing | 1 | D-07 |
| Merge conflict | 1 | D-06 |
| Automated test | 0 | — |

## Severity distribution

| Severity | Count | IDs |
|---|---|---|
| S1 | 3 | D-02, D-05, D-06 |
| S2 | 7 | D-01, D-04, D-07, D-11, D-12, D-13 |
| S3 | 4 | D-03, D-09, D-10, D-15 |
| S4 | 2 | D-08, D-14 |

## Status

| Status | Count |
|---|---|
| Closed | 7 |
| Open | 8 |
