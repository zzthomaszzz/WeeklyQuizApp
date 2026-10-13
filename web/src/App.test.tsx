import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, vi } from 'vitest'
import App from './App'
import { dashboardFixture } from './test/dashboardFixture'

afterEach(() => vi.unstubAllGlobals())

it.each(['student', 'lecturer'] as const)('signs in and opens the %s dashboard with returned data', async role => {
  const user = userEvent.setup()
  const account = { ...dashboardFixture.user, role }
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(account)))
    .mockResolvedValueOnce(new Response(JSON.stringify({ ...dashboardFixture, user: account })))
  vi.stubGlobal('fetch', fetchMock)
  render(<MemoryRouter initialEntries={['/login']}><App /></MemoryRouter>)
  await user.type(screen.getByLabelText('Email'), account.email)
  await user.type(screen.getByLabelText('Password'), 'test-password')
  await user.click(screen.getByRole('button', { name: 'Submit' }))
  expect(await screen.findByRole('heading', { name: role === 'lecturer' ? 'Lecturer dashboard' : 'Weekly quizzes' })).toBeInTheDocument()
  expect(screen.queryByRole('link', { name: 'Sign in' })).not.toBeInTheDocument()
  expect(screen.getByText(account.name)).toBeInTheDocument()
  expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/login')
  expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ email: account.email, password: 'test-password' })
})

it('returns unauthenticated visitors to login', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Please sign in' }), { status: 401 })))
  render(<MemoryRouter initialEntries={['/lecturer']}><App /></MemoryRouter>)
  expect(await screen.findByRole('button', { name: 'Submit' })).toBeInTheDocument()
})

it('redirects a student away from the lecturer route', async () => {
  vi.stubGlobal('fetch', vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify(dashboardFixture)))))
  render(<MemoryRouter initialEntries={['/lecturer']}><App /></MemoryRouter>)
  expect(await screen.findByRole('heading', { name: 'Weekly quizzes' })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Lecturer dashboard' })).not.toBeInTheDocument()
})

it('shows an API error instead of example data', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Database is temporarily unavailable' }), { status: 503 })))
  render(<MemoryRouter initialEntries={['/student']}><App /></MemoryRouter>)
  expect(await screen.findByRole('alert')).toHaveTextContent('Database is temporarily unavailable')
  expect(screen.queryByText('Example 1')).not.toBeInTheDocument()
})

it('keeps failed login on the login page', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Email or password is incorrect' }), { status: 401 })))
  const user = userEvent.setup()
  render(<MemoryRouter initialEntries={['/login']}><App /></MemoryRouter>)
  await user.type(screen.getByLabelText('Email'), 'student@example.test')
  await user.type(screen.getByLabelText('Password'), 'wrong-password')
  await user.click(screen.getByRole('button', { name: 'Submit' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Email or password is incorrect')
  expect(screen.getByRole('button', { name: 'Submit' })).toBeEnabled()
})
