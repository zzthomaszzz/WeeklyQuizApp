import { useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router'
import { ApiError, postJson, request } from '../../api/client'
import type { AttemptResult, QuizQuestion } from '../../api/client'
import { SiteHeader } from '../../components/SiteHeader'
import './TakeQuiz.css'

export function TakeQuizPage() {
  const { quizId } = useParams()

  const [questions, setQuestions] = useState<QuizQuestion[] | null>(null)
  const [selected, setSelected] = useState<Record<number, number>>({})
  const [result, setResult] = useState<AttemptResult | null>(null)
  const [error, setError] = useState('')
  const [unauthorized, setUnauthorized] = useState(false)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    let active = true
    setError('')
    request<QuizQuestion[]>(`/quizzes/${quizId}/questions`)
      .then(loaded => { if (active) setQuestions(loaded) })
      .catch(problem => {
        if (!active) return
        if (problem instanceof ApiError && problem.status === 401) setUnauthorized(true)
        else setError(problem.message)
      })
    return () => { active = false }
  }, [quizId])

  if (unauthorized) return <Navigate to="/login" replace />

  async function submit() {
    if (pending || !questions) return

    const unanswered = questions.filter(question => selected[question.id] === undefined)
    if (unanswered.length > 0) {
      setError('Answer every question before submitting.')
      return
    }

    setPending(true)
    setError('')
    try {
      const graded = await postJson<AttemptResult>(`/quizzes/${quizId}/attempts`, {
        answers: questions.map(question => ({
          question_id: question.id,
          selected_option_id: selected[question.id],
        })),
      })
      setResult(graded)
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'Unable to submit your answers.')
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="dashboard">
      <SiteHeader workspace="Student workspace" />
      <main className="dashboard-main">
        {result ? (
          <Results questions={questions ?? []} result={result} />
        ) : (
          <>
            <div className="page-intro">
              <div>
                <h1>Take the quiz</h1>
                <p className="intro-copy">Choose one answer for each question.</p>
              </div>
            </div>

            <section className="quiz-section" aria-labelledby="questions-title">
              <div className="section-heading">
                <h2 id="questions-title">Questions</h2>
              </div>

              {!questions && !error && <p role="status">Loading the quiz…</p>}
              {error && <p role="alert">{error}</p>}

              {questions && questions.length === 0 && (
                <div className="empty-state">
                  <h3>No questions yet</h3>
                  <p>This quiz has no questions. Check back once your lecturer has added some.</p>
                </div>
              )}

              {questions?.map(question => (
                <fieldset className="question-block" key={question.id}>
                  <legend>
                    <span className="question-number">{question.position}</span>
                    {question.text}
                  </legend>
                  {question.options.map(option => (
                    <label className="option-row" key={option.id}>
                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        value={option.id}
                        checked={selected[question.id] === option.id}
                        onChange={() =>
                          setSelected(current => ({ ...current, [question.id]: option.id }))
                        }
                      />
                      <span>{option.text}</span>
                    </label>
                  ))}
                </fieldset>
              ))}

              {questions && questions.length > 0 && (
                <button type="button" className="submit-button" onClick={submit} disabled={pending}>
                  {pending ? 'Submitting…' : 'Submit answers'}
                </button>
              )}
            </section>
          </>
        )}
        <footer className="dashboard-footer"><span>Weekly Quiz</span></footer>
      </main>
    </div>
  )
}

function Results({ questions, result }: { questions: QuizQuestion[]; result: AttemptResult }) {
  const questionById = new Map(questions.map(question => [question.id, question]))
  const optionById = new Map(
    questions.flatMap(question => question.options).map(option => [option.id, option])
  )

  return (
    <>
      <div className="page-intro">
        <div>
          <h1>Your score</h1>
          <p className="intro-copy">{result.score} out of {result.max_score}</p>
        </div>
      </div>

      <section className="quiz-section" aria-labelledby="results-title">
        <div className="section-heading">
          <h2 id="results-title">Your answers</h2>
        </div>

        {result.answers.map(answer => (
          <article className="result-row" key={answer.question_id}>
            <div className="quiz-detail">
              <h3>{questionById.get(answer.question_id)?.text ?? 'Question'}</h3>
              <p>You chose: {optionById.get(answer.selected_option_id)?.text ?? '—'}</p>
            </div>
            <span className={answer.is_correct ? 'verdict correct' : 'verdict incorrect'}>
              {answer.is_correct ? 'Correct' : 'Incorrect'}
            </span>
          </article>
        ))}

        <Link className="text-button" to="/student">Back to my quizzes</Link>
      </section>
    </>
  )
}
