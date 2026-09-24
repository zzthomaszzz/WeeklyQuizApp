# Weekly Quiz App

Formative weekly multiple-choice quizzes. Lecturers author a quiz each week;
students take it to check their understanding. Quizzes do not count toward
grades.

Third-year Software Quality Assurance group project (ENSE707, AUT).

## Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript (`web/`) |
| Backend | FastAPI + Python 3.13 (`api/`) |
| Database | PostgreSQL |
| Tests | Vitest + React Testing Library, pytest |

## Prerequisites

- Python 3.13
- Node.js 20.19+
- Git

## Setup

```bash
git clone https://github.com/zzthomaszzz/WeeklyQuizApp.git
cd WeeklyQuizApp
```

Backend:

```bash
cd api
python -m venv .venv
.venv/Scripts/pip.exe install -r requirements-dev.txt
```

Frontend:

```bash
cd web
npm install
```

> macOS/Linux: use `.venv/bin/` instead of `.venv/Scripts/`.

## Running

Two terminals.

Backend:

```bash
cd api
.venv/Scripts/uvicorn.exe app.main:app --reload --port 8000
```

Frontend:

```bash
cd web
npm run dev
```

Open http://localhost:5173/login to sign in.

| URL | |
|---|---|
| http://localhost:5173 | app |
| http://127.0.0.1:8000/docs | API docs |

## Testing

```bash
cd web && npm test
```

```bash
cd api
.venv/Scripts/python.exe -m pytest unit_tests -q
.venv/Scripts/python.exe -m pytest tests -q
```

## Common issues

- **`API: failed`** — backend isn't running, or Vite needs restarting after a
  `vite.config.ts` change.
- **`ModuleNotFoundError: No module named 'app'`** — run uvicorn from `api/`,
  not the repo root.
- **`uvicorn: command not found`** — use the full `.venv/Scripts/` path.

## Project structure

```
api/        FastAPI backend
  app/      application code
  tests/
web/        React frontend
  src/
docs/
```

## Docs

- [CLAUDE.md](CLAUDE.md) — architecture and domain rules
- [GIT_WORKFLOW.md](GIT_WORKFLOW.md) — branching, commits, PRs

## Contributing

Nobody commits directly to `main`. Branch, open a PR, get one approval. See
[GIT_WORKFLOW.md](GIT_WORKFLOW.md).

## Database-backed login and dashboards

Open /login and sign in with the email and password of an existing users row.
The server verifies password_hash and reads role from the database:
student -> /student, lecturer -> /lecturer. Direct dashboard visits require
a valid HttpOnly session cookie. No example data is used by the application.

Before starting the backend, configure api/.env (never commit it):
- DATABASE_URL: the existing PostgreSQL/Neon connection string.
- SESSION_SECRET: a random secret of at least 32 characters, shared by all API instances.
- COOKIE_SECURE=false for local HTTP; use true for HTTPS deployment.
- CORS_ORIGINS: JSON array of exact trusted frontend origins (see .env.example).
  Deploy the frontend and /api under the same origin using a proxy or rewrite.
  The current client uses relative /api URLs and same-origin cookies.

Generate a session secret locally with:
`api/.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(48))"`

Current password verification supports bcrypt and Passlib PBKDF2-SHA256 hashes.
Confirm the existing database hash format before live verification; plaintext
passwords are not accepted. Database connection and real-account testing are
deferred until the database service is restored.

Dashboard queries use the supplied users, courses, enrolments and quizzes names.
Students receive their enrolled courses and published quizzes within the opening
and closing window. Lecturers receive courses where lecturer_id matches their
authenticated id and all quizzes in those courses. Password hashes, enrolment
codes, and answer correctness are not returned by these endpoints.

Tests that do not require PostgreSQL:
- From web: npm run test:ci
- From api: .venv/Scripts/python.exe -m pytest unit_tests -q

Unit-test fixtures are isolated from the app and never inserted into PostgreSQL.
The existing api/tests database integration suite still requires TEST_DATABASE_URL.

Run unit_tests and tests in separate processes, as CI does, to isolate their settings.
