import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, vi } from 'vitest'
import { TakeQuizPage } from './TakeQuizPage'

afterEach(() => vi.unstubAllGlobals())

const questions = [
  {
    id: 10,
    quiz_id: 5,
    text: 'Which of these is a black-box technique?',
    topic_tag: 'Testing',
    position: 1,
    options: [
      { id: 101, question_id: 10, text: 'Boundary value analysis', position: 1 },
      { id: 102, question_id: 10, text: 'Statement coverage', position: 2 },
    ],
  },
  {
    id: 11,
    quiz_id: 5,
    text: 'What does CI stand for?',
    topic_tag: 'Process',
    position: 2,
    options: [
      { id: 103, question_id: 11, text: 'Continuous integration', position: 1 },
      { id: 104, question_id: 11, text: 'Code inspection', position: 2 },
    ],
  },
]

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/quizzes/5']}>
      <Routes>
        <Route path="/quizzes/:quizId" element={<TakeQuizPage />} />
        <Route path="/login" element={<h1>Sign in</h1>} />
      </Routes>
    </MemoryRouter>
  )
}

function stubFetch(...responses: Response[]) {
  const mock = vi.fn()
  for (const response of responses) mock.mockResolvedValueOnce(response)
  vi.stubGlobal('fetch', mock)
  return mock
}

const ok = (body: unknown) => new Response(JSON.stringify(body))

it('shows every question with its answer options', async () => {
  stubFetch(ok(questions))
  renderPage()

  expect(await screen.findByText('Which of these is a black-box technique?')).toBeInTheDocument()
  expect(screen.getByRole('radio', { name: 'Boundary value analysis' })).toBeInTheDocument()
  expect(screen.getByRole('radio', { name: 'Code inspection' })).toBeInTheDocument()
})

it('allows only one answer per question', async () => {
  const user = userEvent.setup()
  stubFetch(ok(questions))
  renderPage()

  const first = await screen.findByRole('radio', { name: 'Boundary value analysis' })
  const second = screen.getByRole('radio', { name: 'Statement coverage' })

  await user.click(first)
  expect(first).toBeChecked()

  await user.click(second)
  expect(second).toBeChecked()
  expect(first).not.toBeChecked()
})

it('refuses to submit until every question is answered', async () => {
  const user = userEvent.setup()
  const fetchMock = stubFetch(ok(questions))
  renderPage()

  await user.click(await screen.findByRole('radio', { name: 'Boundary value analysis' }))
  await user.click(screen.getByRole('button', { name: 'Submit answers' }))

  expect(await screen.findByRole('alert')).toHaveTextContent(/every question/i)
  // Only the initial GET; nothing was posted.
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('submits the selected options and shows the score', async () => {
  const user = userEvent.setup()
  const fetchMock = stubFetch(
    ok(questions),
    ok({
      attempt_id: 77,
      score: 1,
      max_score: 2,
      answers: [
        { question_id: 10, selected_option_id: 101, is_correct: true },
        { question_id: 11, selected_option_id: 104, is_correct: false },
      ],
    })
  )
  renderPage()

  await user.click(await screen.findByRole('radio', { name: 'Boundary value analysis' }))
  await user.click(screen.getByRole('radio', { name: 'Code inspection' }))
  await user.click(screen.getByRole('button', { name: 'Submit answers' }))

  expect(await screen.findByRole('heading', { name: /your score/i })).toBeInTheDocument()
  expect(screen.getByText('1 out of 2')).toBeInTheDocument()

  const [path, init] = fetchMock.mock.calls[1]
  expect(path).toBe('/api/quizzes/5/attempts')
  expect(JSON.parse(init.body)).toEqual({
    answers: [
      { question_id: 10, selected_option_id: 101 },
      { question_id: 11, selected_option_id: 104 },
    ],
  })
})

it('marks each answer as right or wrong in the results', async () => {
  const user = userEvent.setup()
  stubFetch(
    ok(questions),
    ok({
      attempt_id: 77,
      score: 1,
      max_score: 2,
      answers: [
        { question_id: 10, selected_option_id: 101, is_correct: true },
        { question_id: 11, selected_option_id: 104, is_correct: false },
      ],
    })
  )
  renderPage()

  await user.click(await screen.findByRole('radio', { name: 'Boundary value analysis' }))
  await user.click(screen.getByRole('radio', { name: 'Code inspection' }))
  await user.click(screen.getByRole('button', { name: 'Submit answers' }))

  await screen.findByRole('heading', { name: /your score/i })
  expect(screen.getByText('Correct')).toBeInTheDocument()
  expect(screen.getByText('Incorrect')).toBeInTheDocument()
})

it('disables the submit button while the attempt is in flight', async () => {
  const user = userEvent.setup()
  const mock = vi.fn().mockResolvedValueOnce(ok(questions)).mockReturnValueOnce(new Promise(() => {}))
  vi.stubGlobal('fetch', mock)
  renderPage()

  await user.click(await screen.findByRole('radio', { name: 'Boundary value analysis' }))
  await user.click(screen.getByRole('radio', { name: 'Code inspection' }))
  await user.click(screen.getByRole('button', { name: 'Submit answers' }))

  expect(await screen.findByRole('button', { name: /submitting/i })).toBeDisabled()
})

it('sends an unauthenticated visitor to the login page', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ detail: 'Please sign in' }), { status: 401 })
  ))
  renderPage()

  expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
})

it('shows the server message when the quiz cannot be loaded', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ detail: 'Quiz not found' }), { status: 404 })
  ))
  renderPage()

  expect(await screen.findByRole('alert')).toHaveTextContent('Quiz not found')
})

it('tells the student when a quiz has no questions yet', async () => {
  stubFetch(ok([]))
  renderPage()

  expect(await screen.findByRole('heading', { name: 'No questions yet' })).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Submit answers' })).not.toBeInTheDocument()
})
