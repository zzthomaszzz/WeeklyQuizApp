# Weekly Quiz App

Third-year Software Quality Assurance group project (3 people, AUT).
Lecturers create weekly MCQ quizzes; students take them to check comprehension.
Formative only — quizzes do not count toward grades.

## Stack
- Frontend: React (Vite + TypeScript) in /web
- Backend: FastAPI (Python 3.12) in /api, deployed as Vercel Python Functions
- DB: PostgreSQL on Neon (prod), local Docker Postgres (dev)
- ORM: SQLAlchemy 2.0 async + Alembic
- Tests: pytest, Vitest + RTL + MSW, Playwright
- CI: GitHub Actions

## Architecture rules
- routers = thin HTTP layer; services = business rules; repositories = SQL only
- Services take repositories as constructor args — never import a DB session directly.
  This is what allows unit tests with fakes and no database.
- Single-choice MCQ only. No written answers.
- Quizzes have max_attempts (NULL = unlimited).
- Students must NEVER receive `is_correct` before submitting — separate
  Pydantic schemas per role, never filter in React.

## Working method
- TDD: failing test first, then implementation.
- Migrations via Alembic files only, never the Neon UI.
- Migrations run in GitHub Actions on main, not on deploy (serverless has no startup hook).
- All work on branches, PR + 1 approval, no direct commits to main.