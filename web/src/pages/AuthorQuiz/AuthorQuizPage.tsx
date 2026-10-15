import { useState } from 'react'
import { Link, Navigate, useParams } from 'react-router'
import { ApiError, postJson } from '../../api/client'
import type { CreatedQuestion, CreatedQuiz } from '../../api/client'
import '../StudentsDashboard/Dashboard.css'
import './AuthorQuiz.css'

const ANSWER_SLOTS = 4
const emptyAnswers = () => Array.from({ length: ANSWER_SLOTS }, () => '')

export function AuthorQuizPage() {
  const { courseId } = useParams()

  const [quiz, setQuiz] = useState<CreatedQuiz | null>(null)
  const [questions, setQuestions] = useState<CreatedQuestion[]>([])
  const [error, setError] = useState('')
  const [unauthorized, setUnauthorized] = useState(false)
  const [pending, setPending] = useState(false)

  const [weekNumber, setWeekNumber] = useState('')
  const [title, setTitle] = useState('')
  const [maxAttempts, setMaxAttempts] = useState('')

  const [questionText, setQuestionText] = useState('')
  const [topicTag, setTopicTag] = useState('')
  const [answers, setAnswers] = useState<string[]>(emptyAnswers)
  const [correctIndex, setCorrectIndex] = useState<number | null>(null)

  if (unauthorized) return <Navigate to="/login" replace />

  function handle(problem: unknown) {
    if (problem instanceof ApiError && problem.status === 401) setUnauthorized(true)
    else setError(problem instanceof Error ? problem.message : 'Something went wrong.')
  }

  async function submitQuiz(event: React.FormEvent) {
    event.preventDefault()
    if (pending) return

    setPending(true)
    setError('')
    try {
      const created = await postJson<CreatedQuiz>(`/courses/${courseId}/quizzes`, {
        week_number: Number(weekNumber),
        title: title.trim(),
        max_attempts: maxAttempts ? Number(maxAttempts) : null,
      })
      setQuiz(created)
    } catch (problem) {
      handle(problem)
    } finally {
      setPending(false)
    }
  }

  async function submitQuestion(event: React.FormEvent) {
    event.preventDefault()
    if (pending || !quiz) return

    const filled = answers
      .map((text, index) => ({ text: text.trim(), index }))
      .filter(answer => answer.text.length > 0)

    if (filled.length < 2) {
      setError('A question needs at least two answers.')
      return
    }
    if (correctIndex === null || !filled.some(answer => answer.index === correctIndex)) {
      setError('Mark one answer as correct before adding the question.')
      return
    }

    setPending(true)
    setError('')
    try {
      const created = await postJson<CreatedQuestion>(`/quizzes/${quiz.id}/questions`, {
        text: questionText.trim(),
        topic_tag: topicTag.trim() || null,
        options: filled.map(answer => ({
          text: answer.text,
          is_correct: answer.index === correctIndex,
        })),
      })
      setQuestions(current => [...current, created])
      setQuestionText('')
      setTopicTag('')
      setAnswers(emptyAnswers())
      setCorrectIndex(null)
    } catch (problem) {
      handle(problem)
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="dashboard">
      <header className="site-header">
        <Link className="brand-link" to="/lecturer">
          <span className="brand-symbol">WQ</span>
          Weekly Quiz
          <span className="brand-divider">/</span>
          <span className="workspace-name">Lecturer workspace</span>
        </Link>
      </header>
      <main className="dashboard-main">
        <div className="page-intro">
          <div>
            <h1>{quiz ? quiz.title : 'New quiz'}</h1>
            <p className="intro-copy">
              {quiz
                ? 'Add questions. The quiz stays a draft until you publish it.'
                : 'Quizzes are created as drafts, so students cannot see them yet.'}
            </p>
          </div>
        </div>

        {error && (
          <section className="quiz-section">
            <p role="alert">{error}</p>
          </section>
        )}

        {!quiz ? (
          <section className="quiz-section" aria-labelledby="details-title">
            <div className="section-heading"><h2 id="details-title">Quiz details</h2></div>
            <form className="author-form" onSubmit={submitQuiz}>
              <label htmlFor="week">Week number</label>
              <input
                id="week" type="number" min={1} required disabled={pending}
                value={weekNumber} onChange={event => setWeekNumber(event.target.value)}
              />

              <label htmlFor="title">Quiz title</label>
              <input
                id="title" type="text" required disabled={pending}
                value={title} onChange={event => setTitle(event.target.value)}
              />

              <label htmlFor="attempts">Attempts allowed (leave blank for unlimited)</label>
              <input
                id="attempts" type="number" min={1} disabled={pending}
                value={maxAttempts} onChange={event => setMaxAttempts(event.target.value)}
              />

              <button type="submit" className="submit-button" disabled={pending}>
                {pending ? 'Creating…' : 'Create draft quiz'}
              </button>
            </form>
          </section>
        ) : (
          <>
            <section className="quiz-section" aria-labelledby="question-title">
              <div className="section-heading"><h2 id="question-title">Add a question</h2></div>
              <form className="author-form" onSubmit={submitQuestion}>
                <label htmlFor="question">Question</label>
                <input
                  id="question" type="text" required disabled={pending}
                  value={questionText} onChange={event => setQuestionText(event.target.value)}
                />

                <label htmlFor="topic">Topic (optional)</label>
                <input
                  id="topic" type="text" disabled={pending}
                  value={topicTag} onChange={event => setTopicTag(event.target.value)}
                />

                <fieldset className="answer-set">
                  <legend>Answers — mark exactly one as correct</legend>
                  {answers.map((answer, index) => (
                    <div className="answer-row" key={index}>
                      <input
                        type="radio"
                        name="correct-answer"
                        id={`correct-${index}`}
                        aria-label={`Answer ${index + 1} is correct`}
                        checked={correctIndex === index}
                        disabled={pending}
                        onChange={() => setCorrectIndex(index)}
                      />
                      <label className="sr-label" htmlFor={`answer-${index}`}>
                        Answer {index + 1}
                      </label>
                      <input
                        id={`answer-${index}`}
                        type="text"
                        placeholder={`Answer ${index + 1}`}
                        disabled={pending}
                        value={answer}
                        onChange={event =>
                          setAnswers(current =>
                            current.map((value, position) =>
                              position === index ? event.target.value : value
                            )
                          )
                        }
                      />
                    </div>
                  ))}
                </fieldset>

                <button type="submit" className="submit-button" disabled={pending}>
                  {pending ? 'Adding…' : 'Add question'}
                </button>
              </form>
            </section>

            <section className="quiz-section" aria-labelledby="added-title">
              <div className="section-heading">
                <h2 id="added-title">Questions in this quiz <span>{questions.length}</span></h2>
              </div>
              {questions.length === 0 ? (
                <div className="empty-state">
                  <h3>No questions yet</h3>
                  <p>Students cannot take a quiz until it has at least one question.</p>
                </div>
              ) : (
                <ol className="added-list" aria-label="Questions in this quiz">
                  {questions.map(question => (
                    <li key={question.id}>
                      <p className="added-question">{question.text}</p>
                      <ul>
                        {question.options.map(option => (
                          <li key={option.id} className={option.is_correct ? 'is-correct' : ''}>
                            {option.text}
                            {option.is_correct && <span className="verdict correct">Correct</span>}
                          </li>
                        ))}
                      </ul>
                    </li>
                  ))}
                </ol>
              )}
              <Link className="text-button" to="/lecturer">Back to my courses</Link>
            </section>
          </>
        )}
        <footer className="dashboard-footer"><span>Weekly Quiz</span></footer>
      </main>
    </div>
  )
}
