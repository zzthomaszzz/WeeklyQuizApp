# Report backlog

Work parked while the project itself is finished. Each item lists what exists
in the repository already, so whoever writes that section knows what they are
drawing on.

Written as a task list, not as report content. Assessment 2 requires all
written report content to be authored by the team.

---

## Assessment tasks not started

### Task 2 — Requirements verification and traceability (5 marks)

A traceability matrix mapping requirements to the features that implement
them, the tests that verify them, and any defects raised against them.

**Material available:**
- Functional and non-functional requirements from Assessment 1
- Domain rules in `CLAUDE.md` (single-choice MCQ only, `is_correct` never
  reaches the browser before submission, `max_attempts`, role separation)
- 77 automated tests across `api/unit_tests`, `api/tests`, and `web/src`
- 18 recorded defects in `DEFECT_REGISTER.md`

**Still needed:** the mapping itself, and a decision on which requirements
are partially implemented or out of scope. Lecturer quiz authoring is the
obvious candidate — there is no `POST` endpoint for quizzes or questions, so
content can only be created by seeding.

### Task 3 — Test execution and final test results (10 marks)

At least 15 test cases with execution results, plus a summary of planned,
executed, passed, failed, blocked and not-run tests.

**Material available:** 77 automated tests. Each needs extracting into a
table with an ID, preconditions, steps, expected and actual result.

| Suite | Count | Needs a database |
|---|---|---|
| `api/unit_tests` | 30 | no |
| `api/tests` | 12 | yes |
| `web/src` | 30 | no |

The brief also asks for positive, negative, boundary and invalid-input
cases. The suites already contain all four — for example an empty
submission, an option belonging to a different question, and an attempt
beyond the limit — so they need identifying rather than writing.

### Task 7 — Quality testing (5 marks)

At least two quality areas, with risk-based justification.

**Security** is the strongest, and already evidenced:
- `is_correct` absent from the student response by construction, not
  filtered afterwards
- httpOnly cookie sessions rather than a token readable by JavaScript
- 404 rather than 403 on inaccessible resources, so responses cannot be
  used to probe for what exists
- Role and ownership checks on every quiz endpoint

**Accessibility** is the natural second: every frontend test queries by role
and label rather than by CSS class, so the suite fails if a control stops
being reachable by keyboard or screen reader. Not yet measured with a tool —
an axe or Lighthouse run would turn this from an argument into evidence.

### Task 8 — Quality metrics and release decision (10 marks)

**Available now:**

| Metric | Value |
|---|---|
| Automated tests | 77 |
| Backend coverage | 81.9% |
| Frontend coverage | 94.5% |
| Coverage gate | 80% backend, 70% frontend |
| Defects recorded | 18 |
| Defects closed | 12 |

**Still needed:** defect severity distribution over time, commit activity per
member, and the release decision itself with its justification.

### Task 9 — AI-assisted development (5 marks)

The brief asks specifically about **GitHub Copilot**. Development used Claude
Code, which is a different tool. Describe what was actually used, and ask the
lecturer if the framing needs clarifying. Do not claim Copilot was used.

### Task 11 — Team contribution (part of lab work, 20 marks)

Per-member contribution statements with GitHub evidence. `git log --author`
and the PR list give the raw data.

### Task 12 — Presentation (10 marks)

15 slides, all members presenting, working demo.

---

## Code work parked

| Item | Why it matters | Defect |
|---|---|---|
| Lecturers cannot create quizzes | No `POST` for quizzes or questions. Content exists only through seeding, so the lecturer dashboard is read-only. Largest remaining functional gap. | — |
| Nothing is deployed | No `vercel.json`, no deployment. A client-side route will 404 on refresh without an SPA rewrite. The demo currently runs on one laptop. | — |
| `routers/quizzes.py` at 39% coverage | Lowest file in the codebase; holds the backend near its 80% floor. | D-12 |
| Alembic never configured | `CLAUDE.md` says migrations go through Alembic. It is in `requirements.txt` but has no config or revision chain, so `migrations/001_add_quiz_max_attempts.sql` is plain SQL. | new |
| Hand-inserted dev data | `TEST707` and `TEST603` in the dev database came from no seed file and have no questions, so four of six quizzes a student sees are empty. | D-09 related |
| Dead branches | `dashboard`, `feat/authentication-api`, `docs/defect-register` all superseded. Salvage the README content from `dashboard` first. | — |
| Unpinned test tooling | `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` have no version constraint. Same exposure that caused D-18 with ruff. | D-18 related |

---

## Defects still open

From `DEFECT_REGISTER.md` after this round of fixes:

- **D-12** — lint gates now run, but `routers/quizzes.py` coverage remains low
- **D-09 (partial)** — seeding works from a clean clone, but the hand-inserted
  dev rows remain

Everything else recorded is closed. Three new entries are owed to the
register and not yet written up:

1. Both quiz `GET` endpoints were readable with no session at all, including
   draft quizzes. Fixed in #31. The ownership check added in #24 was applied
   to `PATCH` only and never to its two siblings.
2. `seed.sql` fails silently. Every statement is an
   `INSERT ... SELECT ... WHERE`, so with no matching users it inserts
   nothing, commits, and exits 0. Nothing reports a problem.
3. Three connection strings across two files, two of them pointing at Neon
   branches whose passwords no longer work. The test suite passed throughout
   because it reads the one file that was current.
