-- 001: add quizzes.max_attempts
--
-- CLAUDE.md specifies "Quizzes have max_attempts (NULL = unlimited)" but the
-- column was never created. schema.sql describes a fresh install only, so
-- existing databases need this applied once.
--
-- CLAUDE.md also says migrations go through Alembic. Alembic is listed in
-- requirements.txt but has never been configured, so there is no revision
-- chain to add this to. Plain SQL until that is set up.
--
-- Safe to re-run.

ALTER TABLE quizzes
    ADD COLUMN IF NOT EXISTS max_attempts INTEGER;

ALTER TABLE quizzes
    DROP CONSTRAINT IF EXISTS chk_quiz_max_attempts;

ALTER TABLE quizzes
    ADD CONSTRAINT chk_quiz_max_attempts
    CHECK (max_attempts IS NULL OR max_attempts > 0);
