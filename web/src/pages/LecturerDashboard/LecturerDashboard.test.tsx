import { dashboardFixture } from '../../test/dashboardFixture'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LecturerDashboard } from './LecturerDashboard'

describe('Lecturer dashboard', () => {
  it('filters quizzes when a lecturer selects a course and clears empty results', async () => {
    const user = userEvent.setup()
    render(<LecturerDashboard data={{ ...dashboardFixture, user: { ...dashboardFixture.user, role: "lecturer" } }} />)
    await user.click(screen.getByRole('button', { name: /ENSE707/ }))
    expect(screen.getByRole('heading', { name: 'Example 1' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Example 2' })).not.toBeInTheDocument()
    await user.type(screen.getByRole('searchbox'), 'Example 2')
    expect(screen.getByText('No quizzes found')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Clear filters' }))
    expect(screen.getByRole('heading', { name: 'Example 2' })).toBeInTheDocument()
    expect(screen.getByLabelText('Course')).toHaveValue('all')
  })
})

