import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, vi } from 'vitest'
import { RegisterPage } from './RegisterPage'

afterEach(() => vi.unstubAllGlobals())

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/student" element={<h1>Weekly quizzes</h1>} />
        <Route path="/lecturer" element={<h1>Lecturer dashboard</h1>} />
      </Routes>
    </MemoryRouter>
  )
}

async function fillForm(user: ReturnType<typeof userEvent.setup>, role?: string) {
  await user.type(screen.getByLabelText('Full name'), 'Thomas Nguyen')
  await user.type(screen.getByLabelText('Email'), 'thomas@example.test')
  await user.type(screen.getByLabelText('Password'), 'long-enough-password')
  if (role) await user.selectOptions(screen.getByLabelText('I am a'), role)
}

it('asks for a name, email, password and role', () => {
  renderPage()

  expect(screen.getByLabelText('Full name')).toBeInTheDocument()
  expect(screen.getByLabelText('Email')).toBeInTheDocument()
  expect(screen.getByLabelText('Password')).toBeInTheDocument()
  expect(screen.getByLabelText('I am a')).toBeInTheDocument()
})

it('masks the password field', () => {
  renderPage()

  expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'password')
})

it('creates a student account and opens the student dashboard', async () => {
  const user = userEvent.setup()
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ id: 7, email: 'thomas@example.test', name: 'Thomas Nguyen', role: 'student' }), { status: 201 })
  )
  vi.stubGlobal('fetch', fetchMock)
  renderPage()

  await fillForm(user, 'student')
  await user.click(screen.getByRole('button', { name: 'Create account' }))

  expect(await screen.findByRole('heading', { name: 'Weekly quizzes' })).toBeInTheDocument()

  const [path, init] = fetchMock.mock.calls[0]
  expect(path).toBe('/api/auth/register')
  expect(JSON.parse(init.body)).toEqual({
    name: 'Thomas Nguyen',
    email: 'thomas@example.test',
    password: 'long-enough-password',
    role: 'student',
  })
})

it('sends a new lecturer to the lecturer dashboard', async () => {
  const user = userEvent.setup()
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ id: 8, email: 'thomas@example.test', name: 'Thomas Nguyen', role: 'lecturer' }), { status: 201 })
  ))
  renderPage()

  await fillForm(user, 'lecturer')
  await user.click(screen.getByRole('button', { name: 'Create account' }))

  expect(await screen.findByRole('heading', { name: 'Lecturer dashboard' })).toBeInTheDocument()
})

it('shows the server message when the email is already registered', async () => {
  const user = userEvent.setup()
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(
    new Response(JSON.stringify({ detail: 'Email is already registered' }), { status: 409 })
  ))
  renderPage()

  await fillForm(user, 'student')
  await user.click(screen.getByRole('button', { name: 'Create account' }))

  expect(await screen.findByRole('alert')).toHaveTextContent('Email is already registered')
  expect(screen.getByRole('button', { name: 'Create account' })).toBeEnabled()
})

it('links back to the login page', () => {
  renderPage()

  expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login')
})
