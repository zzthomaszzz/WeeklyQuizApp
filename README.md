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

Copy `api/.env.example` to `api/.env` and fill in the values. The backend
will not start without `DATABASE_URL`, and login returns 503 without a
`SESSION_SECRET` of at least 32 characters.

The integration tests use a **separate** database and read it from
`api/.env.test`, not `api/.env`:

```
TEST_DATABASE_URL=postgresql+asyncpg://username:password@hostname/database
```

Then seed it — user accounts first, because the sample data looks them up
by email:

```bash
psql "$TEST_DATABASE_URL" -f database/seed-users.example.sql
psql "$TEST_DATABASE_URL" -f database/seed.sql
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

Open http://localhost:5173 — it should show `API: ok`.

| URL | |
|---|---|
| http://localhost:5173 | app |
| http://127.0.0.1:8000/docs | API docs |

## Testing

Frontend:

```bash
cd web && npm test
```

Backend. These run as two separate processes, exactly as CI does — the unit
suite sets a dummy `DATABASE_URL` that must not leak into the integration
suite:

```bash
cd api
.venv/Scripts/python.exe -m pytest unit_tests -q
.venv/Scripts/python.exe -m pytest tests -q
```

`unit_tests` needs no database. `tests` needs `TEST_DATABASE_URL`.

Linting and coverage, which CI also enforces:

```bash
cd web && npm run lint && npm run test:coverage
cd api && .venv/Scripts/python.exe -m ruff check .
```

## Common issues

- **`API: failed`** — backend isn't running, or Vite needs restarting after a
  `vite.config.ts` change.
- **`ModuleNotFoundError: No module named 'app'`** — run uvicorn from `api/`,
  not the repo root.
- **`uvicorn: command not found`** — use the full `.venv/Scripts/` path.
- **`Login is not configured on the server` (503)** — `SESSION_SECRET` is
  missing from `api/.env`, or is shorter than 32 characters.
- **`TEST_DATABASE_URL is missing`** — create `api/.env.test`. The test
  harness reads that file, not `api/.env`.
- **`password authentication failed`** — the connection string is stale.
  Neon issues a password per branch, so a string copied from another branch
  will not work.

## Project structure

```
api/        FastAPI backend
  app/      application code
  tests/
web/        React frontend
  src/
docs/
```

## Database

`api/database/schema.sql` creates a fresh database. `migrations/` holds
changes to apply to databases that already exist — run them in order.

Seeding is two files, in this order:

```bash
psql "$DATABASE_URL" -f api/database/seed-users.example.sql
psql "$DATABASE_URL" -f api/database/seed.sql
```

The sample accounts all use the password `demo-password-2026`. They are for
development and test databases only.

## Docs

- [CLAUDE.md](CLAUDE.md) — architecture and domain rules
- [GIT_WORKFLOW.md](GIT_WORKFLOW.md) — branching, commits, PRs

## Contributing

Nobody commits directly to `main`. Branch, open a PR, get one approval. See
[GIT_WORKFLOW.md](GIT_WORKFLOW.md).
