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

Open http://localhost:5173 — it should show `API: ok`.

| URL | |
|---|---|
| http://localhost:5173 | app |
| http://127.0.0.1:8000/docs | API docs |

## Testing

```bash
cd web && npm test
```

```bash
cd api && .venv/Scripts/pytest.exe
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
