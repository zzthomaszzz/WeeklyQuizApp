class CourseNotAvailable(Exception):
    """The course does not exist, or is not taught by this lecturer. One
    exception for both, so the response cannot be used to probe which."""


class QuizNotAvailable(Exception):
    """The quiz does not exist, or belongs to another lecturer's course."""


class AuthoringService:
    """Rules for creating quiz content. Takes a repository as a constructor
    arg so unit tests can supply a fake and run with no database."""

    def __init__(self, repository):
        self.repository = repository

    async def create_quiz(self, course_id, lecturer_id, fields):
        course = await self.repository.course_owned_by(course_id, lecturer_id)
        if course is None:
            raise CourseNotAvailable()

        # A quiz always starts as a draft. Publishing is a separate,
        # deliberate step through PATCH.
        return await self.repository.create_quiz(course_id=course_id, **fields)

    async def add_question(self, quiz_id, lecturer_id, text, topic_tag, options):
        quiz = await self.repository.quiz_owned_by(quiz_id, lecturer_id)
        if quiz is None:
            raise QuizNotAvailable()

        position = await self.repository.next_question_position(quiz_id)

        return await self.repository.create_question(
            quiz_id=quiz_id,
            question_text=text,
            topic_tag=topic_tag,
            position=position,
            options=options,
        )
