import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, vi } from 'vitest'
import { AuthorQuizPage } from './AuthorQuizPage'

afterEach(() => vi.unstubAllGlobals())

const ok = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status })

const CREATED_QUIZ = {
  id: 50,
  course_id: 7,
  week_number: 3,
  title: 'Week 3 — Test Design',
  status: 'draft',
  max_attempts: null,
}

const CREATED_QUESTION = {
  id: 60,
  quiz_id: 50,
  text: 'Which of these is a black-box technique?',
  topic_tag: 'Testing',
  position: 1,
  options: [
    { id: 101, text: 'Boundary value analysis', is_correct: true, position: 1 },
    { id: 102, text: 'Statement coverage', is_correct: false, position: 2 },
  ],
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/lecturer/courses/7/quizzes/new']}>
      <Routes>
        <Route path="/lecturer/courses/:courseId/quizzes/new" element={<AuthorQuizPage />} />
        <Route path="/login" element={<h1>Sign in</h1>} />
      </Routes>
    </MemoryRouter>
  )
}

async function createQuiz(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Week number'), '3')
  await user.type(screen.getByLabelText('Quiz title'), 'Week 3 — Test Design')
  await user.click(screen.getByRole('button', { name: 'Create draft quiz' }))
}

async function fillQuestion(user: ReturnType<typeof userEvent.setup>) {
  await user.type(
    screen.getByLabelText('Question'),
    'Which of these is a black-box technique?'
  )
  await user.type(screen.getByLabelText('Answer 1'), 'Boundary value analysis')
  await user.type(screen.getByLabelText('Answer 2'), 'Statement coverage')
  await user.click(screen.getByRole('radio', { name: 'Answer 1 is correct' }))
}

it('asks for the quiz details first', () => {
  vi.stubGlobal('fetch', vi.fn())
  renderPage()

  expect(screen.getByLabelText('Week number')).toBeInTheDocument()
  expect(screen.getByLabelText('Quiz title')).toBeInTheDocument()
  expect(screen.queryByLabelText('Question')).not.toBeInTheDocument()
})

it('creates the quiz as a draft and moves on to questions', async () => {
  const user = userEvent.setup()
  const fetchMock = vi.fn().mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
  vi.stubGlobal('fetch', fetchMock)
  renderPage()

  await createQuiz(user)

  expect(await screen.findByLabelText('Question')).toBeInTheDocument()

  const [path, init] = fetchMock.mock.calls[0]
  expect(path).toBe('/api/courses/7/quizzes')
  expect(JSON.parse(init.body)).toEqual({
    week_number: 3,
    title: 'Week 3 — Test Design',
    max_attempts: null,
  })
})

it('sends an attempt limit when one is given', async () => {
  const user = userEvent.setup()
  const fetchMock = vi.fn().mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
  vi.stubGlobal('fetch', fetchMock)
  renderPage()

  await user.type(screen.getByLabelText('Week number'), '3')
  await user.type(screen.getByLabelText('Quiz title'), 'Week 3 — Test Design')
  await user.type(screen.getByLabelText('Attempts allowed (leave blank for unlimited)'), '2')
  await user.click(screen.getByRole('button', { name: 'Create draft quiz' }))

  await screen.findByLabelText('Question')
  expect(JSON.parse(fetchMock.mock.calls[0][1].body).max_attempts).toBe(2)
})

it('adds a question with its answers and marks one correct', async () => {
  const user = userEvent.setup()
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
    .mockResolvedValueOnce(ok(CREATED_QUESTION, 201))
  vi.stubGlobal('fetch', fetchMock)
  renderPage()

  await createQuiz(user)
  await fillQuestion(user)
  await user.click(screen.getByRole('button', { name: 'Add question' }))

  await screen.findByText('Which of these is a black-box technique?')

  const [path, init] = fetchMock.mock.calls[1]
  expect(path).toBe('/api/quizzes/50/questions')
  expect(JSON.parse(init.body)).toEqual({
    text: 'Which of these is a black-box technique?',
    topic_tag: null,
    options: [
      { text: 'Boundary value analysis', is_correct: true },
      { text: 'Statement coverage', is_correct: false },
    ],
  })
})

it('drops blank answer rows rather than sending them', async () => {
  const user = userEvent.setup()
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
    .mockResolvedValueOnce(ok(CREATED_QUESTION, 201))
  vi.stubGlobal('fetch', fetchMock)
  renderPage()

  await createQuiz(user)
  await fillQuestion(user)
  await user.click(screen.getByRole('button', { name: 'Add question' }))

  await screen.findByText('Which of these is a black-box technique?')
  // Answers 3 and 4 were left empty.
  expect(JSON.parse(fetchMock.mock.calls[1][1].body).options).toHaveLength(2)
})

it('refuses to add a question with fewer than two answers', async () => {
  const user = userEvent.setup()
  const fetchMock = vi.fn().mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
  vi.stubGlobal('fetch', fetchMock)
  renderPage()

  await createQuiz(user)
  await user.type(screen.getByLabelText('Question'), 'Only one answer here')
  await user.type(screen.getByLabelText('Answer 1'), 'The only one')
  await user.click(screen.getByRole('radio', { name: 'Answer 1 is correct' }))
  await user.click(screen.getByRole('button', { name: 'Add question' }))

  expect(await screen.findByRole('alert')).toHaveTextContent(/two answers/i)
  // Only the quiz was created; no question was posted.
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('refuses to add a question before an answer is marked correct', async () => {
  const user = userEvent.setup()
  const fetchMock = vi.fn().mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
  vi.stubGlobal('fetch', fetchMock)
  renderPage()

  await createQuiz(user)
  await user.type(screen.getByLabelText('Question'), 'Nothing marked correct')
  await user.type(screen.getByLabelText('Answer 1'), 'First')
  await user.type(screen.getByLabelText('Answer 2'), 'Second')
  await user.click(screen.getByRole('button', { name: 'Add question' }))

  expect(await screen.findByRole('alert')).toHaveTextContent(/correct/i)
  expect(fetchMock).toHaveBeenCalledTimes(1)
})

it('lists the questions added so far', async () => {
  const user = userEvent.setup()
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
      .mockResolvedValueOnce(ok(CREATED_QUESTION, 201))
  )
  renderPage()

  await createQuiz(user)
  await fillQuestion(user)
  await user.click(screen.getByRole('button', { name: 'Add question' }))

  const list = await screen.findByRole('list', { name: /questions in this quiz/i })
  expect(within(list).getByText('Which of these is a black-box technique?')).toBeInTheDocument()
  expect(within(list).getByText('Boundary value analysis')).toBeInTheDocument()
})

it('clears the question form after a question is added', async () => {
  const user = userEvent.setup()
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValueOnce(ok(CREATED_QUIZ, 201))
      .mockResolvedValueOnce(ok(CREATED_QUESTION, 201))
  )
  renderPage()

  await createQuiz(user)
  await fillQuestion(user)
  await user.click(screen.getByRole('button', { name: 'Add question' }))

  await screen.findByRole('list', { name: /questions in this quiz/i })
  expect(screen.getByLabelText('Question')).toHaveValue('')
  expect(screen.getByLabelText('Answer 1')).toHaveValue('')
})

it('shows the server message when the course is not the lecturer own', async () => {
  const user = userEvent.setup()
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValueOnce(ok({ detail: 'Course not found' }, 404))
  )
  renderPage()

  await createQuiz(user)

  expect(await screen.findByRole('alert')).toHaveTextContent('Course not found')
})

it('sends an unauthenticated visitor to the login page', async () => {
  const user = userEvent.setup()
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValueOnce(ok({ detail: 'Please sign in' }, 401))
  )
  renderPage()

  await createQuiz(user)

  expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
})
