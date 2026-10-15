class QuizNotAvailable(Exception):
    """The quiz does not exist, is not published, is outside its window, or
    the student is not enrolled in its course. One exception for all four, so
    the response cannot be used to probe which."""


class InvalidSubmission(Exception):
    """The submission does not match the quiz it claims to answer."""


class AttemptService:
    """Scoring rules for a submitted quiz. Takes a repository so unit tests
    can supply a fake and run with no database."""

    def __init__(self, repository):
        self.repository = repository

    async def submit(self, quiz_id, student_id, answers):
        quiz = await self.repository.quiz_open_for_student(quiz_id, student_id)
        if quiz is None:
            raise QuizNotAvailable()

        options_by_question = self.build_options(
            await self.repository.grading_key(quiz_id)
        )
        if not options_by_question:
            raise InvalidSubmission("This quiz has no questions yet.")

        selections = self.collect_selections(answers)

        if set(selections) != set(options_by_question):
            raise InvalidSubmission(
                "Answer every question in the quiz exactly once."
            )

        graded = self.grade(selections, options_by_question)
        score = sum(1 for answer in graded if answer["is_correct"])
        max_score = len(options_by_question)

        attempt_id = await self.repository.save_attempt(
            quiz_id, student_id, score, max_score, graded
        )

        return {
            "attempt_id": attempt_id,
            "score": score,
            "max_score": max_score,
            "answers": graded,
        }

    def build_options(self, grading_key):
        options_by_question = {}
        for row in grading_key:
            question = options_by_question.setdefault(row["question_id"], {})
            question[row["option_id"]] = row["is_correct"]
        return options_by_question

    def collect_selections(self, answers):
        selections = {}
        for answer in answers:
            question_id = answer["question_id"]
            if question_id in selections:
                raise InvalidSubmission(
                    "Each question can only be answered once."
                )
            selections[question_id] = answer["selected_option_id"]
        return selections

    def grade(self, selections, options_by_question):
        graded = []
        for question_id, option_id in selections.items():
            options = options_by_question[question_id]

            if option_id not in options:
                raise InvalidSubmission(
                    "An answer selected an option that does not belong to "
                    "its question."
                )

            graded.append(
                {
                    "question_id": question_id,
                    "selected_option_id": option_id,
                    "is_correct": options[option_id],
                }
            )
        return graded
