
-- WeeklyQuizApp sample database seed
-- TEST DATABASE ONLY
-- Run seed-users.local.sql first to create the sample accounts.

BEGIN;

-- =====================================================
-- 1. SAMPLE COURSE
-- =====================================================

INSERT INTO courses (
    code,
    name,
    lecturer_id,
    enrol_code
)
SELECT
    'SDEV101',
    'Introduction to Software Development',
    id,
    'DEMO-SDEV101'
FROM users
WHERE email = 'lecturer.demo@example.com'
    AND role = 'lecturer'
ON CONFLICT (enrol_code) DO NOTHING;


-- =====================================================
-- 2. SAMPLE ENROLMENTS
-- Enrol all 10 sample students in the course.
-- =====================================================

INSERT INTO enrolments (
    student_id,
    course_id
)
SELECT
    users.id,
    courses.id
FROM users
CROSS JOIN courses
WHERE users.email IN (
    'student1.demo@example.com',
    'student2.demo@example.com',
    'james.wilson.demo@example.com',
    'mei.chen.demo@example.com',
    'haruto.sato.demo@example.com',
    'aisha.rahman.demo@example.com',
    'minjun.park.demo@example.com',
    'anika.patel.demo@example.com',
    'daniel.reyes.demo@example.com',
    'sophia.martinez.demo@example.com'
)
AND users.role = 'student'
AND courses.enrol_code = 'DEMO-SDEV101'
ON CONFLICT (student_id, course_id) DO NOTHING;


-- =====================================================
-- 3. SAMPLE WEEKLY QUIZZES
-- =====================================================

INSERT INTO quizzes (
    course_id,
    week_number,
    title,
    status,
    opens_at,
    closes_at
)
SELECT
    courses.id,
    quiz_data.week_number,
    quiz_data.title,
    CAST(quiz_data.status AS quiz_status),
    quiz_data.opens_at,
    quiz_data.closes_at
FROM courses
CROSS JOIN (
    VALUES
        (
            1,
            'Week 1 - Software Development Basics',
            'published',
            CURRENT_TIMESTAMP - INTERVAL '1 day',
            CURRENT_TIMESTAMP + INTERVAL '7 days'
        ),
        (
            2,
            'Week 2 - Software Testing Fundamentals',
            'published',
            CURRENT_TIMESTAMP - INTERVAL '1 day',
            CURRENT_TIMESTAMP + INTERVAL '14 days'
        )
) AS quiz_data (
    week_number,
    title,
    status,
    opens_at,
    closes_at
)
WHERE courses.enrol_code = 'DEMO-SDEV101'
AND NOT EXISTS (
    SELECT 1
    FROM quizzes
    WHERE quizzes.course_id = courses.id
      AND quizzes.week_number = quiz_data.week_number
      AND quizzes.title = quiz_data.title
);


-- =====================================================
-- 4. SAMPLE QUIZ QUESTIONS
-- Two questions per quiz.
-- =====================================================

INSERT INTO questions (
    quiz_id,
    text,
    topic_tag,
    position
)
SELECT
    quizzes.id,
    question_data.question_text,
    question_data.topic_tag,
    question_data.position
FROM courses
JOIN quizzes
    ON quizzes.course_id = courses.id
CROSS JOIN (
    VALUES
        (
            1,
            1,
            'What does SDLC stand for?',
            'Software Development',
            'Week 1 - Software Development Basics'
        ),
        (
            1,
            2,
            'Which development methodology uses short iterations called sprints?',
            'Software Development',
            'Week 1 - Software Development Basics'
        ),
        (
            2,
            1,
            'What is the main purpose of software testing?',
            'Software Testing',
            'Week 2 - Software Testing Fundamentals'
        ),
        (
            2,
            2,
            'Which type of testing focuses on individual functions or components?',
            'Software Testing',
            'Week 2 - Software Testing Fundamentals'
        )
) AS question_data (
    week_number,
    position,
    question_text,
    topic_tag,
    quiz_title
)
WHERE courses.enrol_code = 'DEMO-SDEV101'
    AND quizzes.week_number = question_data.week_number
    AND quizzes.title = question_data.quiz_title
ON CONFLICT (quiz_id, position) DO NOTHING;


-- =====================================================
-- 5. SAMPLE MULTIPLE-CHOICE OPTIONS
-- Four options per question.
-- Position 1 = A, 2 = B, 3 = C, 4 = D.
-- =====================================================

INSERT INTO options (
    question_id,
    text,
    is_correct,
    position
)
SELECT
    questions.id,
    option_data.option_text,
    option_data.is_correct,
    option_data.option_position
FROM courses
JOIN quizzes
    ON quizzes.course_id = courses.id
JOIN questions
    ON questions.quiz_id = quizzes.id
JOIN (
    VALUES
        -- Week 1, Question 1: SDLC
        (1, 1, 1, 'Software Development Life Cycle', TRUE),
        (1, 1, 2, 'System Design Logic Code', FALSE),
        (1, 1, 3, 'Software Data Learning Centre', FALSE),
        (1, 1, 4, 'System Development Language Code', FALSE),

        -- Week 1, Question 2: Sprints
        (1, 2, 1, 'Waterfall', FALSE),
        (1, 2, 2, 'Scrum', TRUE),
        (1, 2, 3, 'V-Model', FALSE),
        (1, 2, 4, 'Spiral Model', FALSE),

        -- Week 2, Question 1: Software testing
        (2, 1, 1, 'To remove the need for documentation', FALSE),
        (2, 1, 2, 'To guarantee that software has no defects', FALSE),
        (2, 1, 3, 'To evaluate software and identify defects', TRUE),
        (2, 1, 4, 'To replace the development process', FALSE),

        -- Week 2, Question 2: Unit testing
        (2, 2, 1, 'System testing', FALSE),
        (2, 2, 2, 'Acceptance testing', FALSE),
        (2, 2, 3, 'Unit testing', TRUE),
        (2, 2, 4, 'Performance testing', FALSE)
) AS option_data (
    week_number,
    question_position,
    option_position,
    option_text,
    is_correct
)
    ON quizzes.week_number = option_data.week_number
    AND questions.position = option_data.question_position
    AND (
        (
            option_data.week_number = 1
            AND quizzes.title = 'Week 1 - Software Development Basics'
        )
        OR
        (
            option_data.week_number = 2
            AND quizzes.title = 'Week 2 - Software Testing Fundamentals'
        )
    )
WHERE courses.enrol_code = 'DEMO-SDEV101'
ON CONFLICT (question_id, position) DO NOTHING;


-- =====================================================
-- 6. SAMPLE QUIZ ATTEMPT
-- Shan Carido completes the Week 1 quiz.
-- =====================================================

INSERT INTO attempts (
    quiz_id,
    student_id,
    submitted_at,
    score,
    max_score
)
SELECT
    quizzes.id,
    users.id,
    quizzes.opens_at + INTERVAL '2 hours',
    2,
    2
FROM quizzes
JOIN courses
    ON quizzes.course_id = courses.id
CROSS JOIN users
WHERE courses.enrol_code = 'DEMO-SDEV101'
    AND quizzes.week_number = 1
    AND quizzes.title = 'Week 1 - Software Development Basics'
    AND users.email = 'student1.demo@example.com'
    AND users.role = 'student'
    AND NOT EXISTS (
        SELECT 1
        FROM attempts
        WHERE attempts.quiz_id = quizzes.id
          AND attempts.student_id = users.id
          AND attempts.submitted_at =
              quizzes.opens_at + INTERVAL '2 hours'
    );


-- =====================================================
-- 7. SAMPLE STUDENT ANSWERS
-- Shan Carido answers both Week 1 questions correctly.
-- =====================================================

INSERT INTO answers (
    attempt_id,
    question_id,
    selected_option_id,
    is_correct
)
SELECT
    attempts.id,
    questions.id,
    options.id,
    options.is_correct
FROM courses
JOIN quizzes
    ON quizzes.course_id = courses.id
JOIN attempts
    ON attempts.quiz_id = quizzes.id
JOIN users
    ON users.id = attempts.student_id
JOIN questions
    ON questions.quiz_id = quizzes.id
JOIN (
    VALUES
        (1, 1),
        (2, 2)
) AS selected_answers (
    question_position,
    option_position
)
    ON questions.position = selected_answers.question_position
JOIN options
    ON options.question_id = questions.id
    AND options.position = selected_answers.option_position
WHERE courses.enrol_code = 'DEMO-SDEV101'
    AND quizzes.week_number = 1
    AND quizzes.title = 'Week 1 - Software Development Basics'
    AND users.email = 'student1.demo@example.com'
    AND attempts.submitted_at =
        quizzes.opens_at + INTERVAL '2 hours'
ON CONFLICT (attempt_id, question_id) DO NOTHING;

COMMIT;