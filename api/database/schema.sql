-- Weekly Quiz App database schema
-- PostgreSQL / Neon

-- Assumed enum values:
-- user_role: student, lecturer
-- quiz_status: draft, published, closed

CREATE TYPE user_role AS ENUM (
    'student',
    'lecturer'
);

CREATE TYPE quiz_status AS ENUM (
    'draft',
    'published',
    'closed'
);

-- USERS
CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    password_hash TEXT NOT NULL,
    role user_role NOT NULL
);

-- COURSES
CREATE TABLE courses (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(30) NOT NULL,
    name VARCHAR(200) NOT NULL,
    lecturer_id BIGINT NOT NULL,
    enrol_code VARCHAR(50) NOT NULL UNIQUE,

    CONSTRAINT fk_courses_lecturer
        FOREIGN KEY (lecturer_id)
        REFERENCES users(id)
        ON DELETE RESTRICT
);

-- ENROLMENTS
CREATE TABLE enrolments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id BIGINT NOT NULL,
    course_id BIGINT NOT NULL,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_enrolments_student
        FOREIGN KEY (student_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_enrolments_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_student_course
        UNIQUE (student_id, course_id)
);

-- QUIZZES
CREATE TABLE quizzes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    course_id BIGINT NOT NULL,
    week_number INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    material_url TEXT,
    status quiz_status NOT NULL DEFAULT 'draft',
    opens_at TIMESTAMPTZ,
    closes_at TIMESTAMPTZ,

    CONSTRAINT fk_quizzes_course
        FOREIGN KEY (course_id)
        REFERENCES courses(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_quiz_week
        CHECK (week_number > 0),

    CONSTRAINT chk_quiz_dates
        CHECK (
            closes_at IS NULL
            OR opens_at IS NULL
            OR closes_at > opens_at
        )
);

-- QUESTIONS
CREATE TABLE questions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quiz_id BIGINT NOT NULL,
    text TEXT NOT NULL,
    topic_tag VARCHAR(100),
    position INTEGER NOT NULL,

    CONSTRAINT fk_questions_quiz
        FOREIGN KEY (quiz_id)
        REFERENCES quizzes(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_question_position
        CHECK (position > 0),

    CONSTRAINT uq_question_position
        UNIQUE (quiz_id, position)
);

-- OPTIONS
CREATE TABLE options (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    question_id BIGINT NOT NULL,
    text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    position INTEGER NOT NULL,

    CONSTRAINT fk_options_question
        FOREIGN KEY (question_id)
        REFERENCES questions(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_option_position
        CHECK (position > 0),

    CONSTRAINT uq_option_position
        UNIQUE (question_id, position),

    CONSTRAINT uq_option_question
        UNIQUE (id, question_id)
);

-- Only one correct option per question
CREATE UNIQUE INDEX uq_one_correct_option
    ON options(question_id)
    WHERE is_correct = TRUE;

-- ATTEMPTS
CREATE TABLE attempts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    quiz_id BIGINT NOT NULL,
    student_id BIGINT NOT NULL,
    submitted_at TIMESTAMPTZ,
    score INTEGER NOT NULL DEFAULT 0,
    max_score INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT fk_attempts_quiz
        FOREIGN KEY (quiz_id)
        REFERENCES quizzes(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_attempts_student
        FOREIGN KEY (student_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_attempt_score
        CHECK (
            score >= 0
            AND max_score >= 0
            AND score <= max_score
        )
);

-- ANSWERS
CREATE TABLE answers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    attempt_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    selected_option_id BIGINT NOT NULL,
    is_correct BOOLEAN NOT NULL,

    CONSTRAINT fk_answers_attempt
        FOREIGN KEY (attempt_id)
        REFERENCES attempts(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_answers_question
        FOREIGN KEY (question_id)
        REFERENCES questions(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_answers_selected_option
        FOREIGN KEY (selected_option_id, question_id)
        REFERENCES options(id, question_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_attempt_question
        UNIQUE (attempt_id, question_id)
);

-- Indexes for common searches
CREATE INDEX idx_courses_lecturer
    ON courses(lecturer_id);

CREATE INDEX idx_enrolments_student
    ON enrolments(student_id);

CREATE INDEX idx_enrolments_course
    ON enrolments(course_id);

CREATE INDEX idx_quizzes_course
    ON quizzes(course_id);

CREATE INDEX idx_questions_quiz
    ON questions(quiz_id);

CREATE INDEX idx_options_question
    ON options(question_id);

CREATE INDEX idx_attempts_quiz
    ON attempts(quiz_id);

CREATE INDEX idx_attempts_student
    ON attempts(student_id);

CREATE INDEX idx_answers_attempt
    ON answers(attempt_id);