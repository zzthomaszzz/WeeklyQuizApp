import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router'
import { afterEach, vi } from 'vitest'
import { SiteHeader } from './SiteHeader'

afterEach(() => vi.unstubAllGlobals())

function renderHeader(name = 'Test Student') {
  return render(
    <MemoryRouter initialEntries={['/student']}>
      <Routes>
        <Route path="/student" element={<SiteHeader workspace="Student workspace" userName={name} />} />
        <Route path="/login" element={<h1>Sign in</h1>} />
      </Routes>
    </MemoryRouter>
  )
}

it('shows who is signed in', () => {
  renderHeader('Thomas Nguyen')

  expect(screen.getByText('Thomas Nguyen')).toBeInTheDocument()
})

it('offers a sign out button', () => {
  renderHeader()

  expect(screen.getByRole('button', { name: 'Sign out' })).toBeInTheDocument()
})

it('clears the session and returns to login on sign out', async () => {
  const user = userEvent.setup()
  const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }))
  vi.stubGlobal('fetch', fetchMock)
  renderHeader()

  await user.click(screen.getByRole('button', { name: 'Sign out' }))

  expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()

  const [path, init] = fetchMock.mock.calls[0]
  expect(path).toBe('/api/auth/logout')
  expect(init.method).toBe('POST')
})

it('returns to login even if the logout request fails', async () => {
  const user = userEvent.setup()
  // The cookie is httpOnly, so the client cannot clear it itself. Sending
  // the user to login regardless is better than stranding them on a page
  // they can no longer use.
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
  renderHeader()

  await user.click(screen.getByRole('button', { name: 'Sign out' }))

  expect(await screen.findByRole('heading', { name: 'Sign in' })).toBeInTheDocument()
})
